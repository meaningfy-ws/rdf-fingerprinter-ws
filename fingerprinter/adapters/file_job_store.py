"""``JobStore`` on the file system: one folder per job under the reports folder (design D-3, D-5)."""

import dataclasses
import json
import os
import shutil
import zipfile
from pathlib import Path

from fingerprinter.domain.exceptions import FormatNotAvailable, JobNotFound
from fingerprinter.domain.model import FingerprintOutcome, JobRecord, JobState, ReportFormat

META_FILE = "meta.json"
REPORT_ZIP = "report.zip"


def _zip(root: Path, target: Path, folder_names: list[str]) -> None:
    """Zip the given folders of ``root``, each file under its path relative to ``root``."""
    # replace, not write: a download never finds a half-written zip
    temporary = target.with_suffix(".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in folder_names:
            for path in sorted((root / name).rglob("*")):
                if path.is_file():
                    archive.write(path, arcname=path.relative_to(root).as_posix())
    os.replace(temporary, target)


def _format_zip(job_folder: Path, report_format: ReportFormat) -> Path:
    """The download of a format that has several files: one zip beside ``report.zip``."""
    return job_folder / f"{job_folder.name}-{report_format.value}.zip"


class FileJobStore:
    def __init__(self, reports_folder: Path):
        self.reports_folder = reports_folder

    def _folder(self, job_id: str) -> Path:
        if job_id in ("", ".", "..") or Path(job_id).name != job_id:
            raise JobNotFound(job_id)
        return self.reports_folder / job_id

    def _write(self, record: JobRecord) -> None:
        meta = self._folder(record.id) / META_FILE
        # replace, not write: the API reads the record while the worker updates it
        temporary = meta.with_suffix(".tmp")
        temporary.write_text(json.dumps(record.to_dict()))
        os.replace(temporary, meta)

    def create(self, record: JobRecord) -> None:
        self._folder(record.id).mkdir(parents=True, exist_ok=False)
        self._write(record)

    def get(self, job_id: str) -> JobRecord:
        meta = self._folder(job_id) / META_FILE
        try:
            return JobRecord.from_dict(json.loads(meta.read_text()))
        except FileNotFoundError:
            raise JobNotFound(job_id) from None

    def list(self) -> list[JobRecord]:
        if not self.reports_folder.is_dir():
            return []
        records = []
        for folder in self.reports_folder.iterdir():
            try:
                records.append(self.get(folder.name))
            except (JobNotFound, NotADirectoryError):  # deleted meanwhile, or not a job folder
                continue
        return sorted(records, key=lambda record: record.created_at)

    def set_state(
        self,
        job_id: str,
        state: JobState,
        reason: str | None = None,
        failures: tuple[str, ...] = (),
    ) -> None:
        record = self.get(job_id)
        self._write(dataclasses.replace(record, state=state, reason=reason, failures=failures))

    def save_outputs(self, job_id: str, outcome: FingerprintOutcome) -> None:
        record = self.get(job_id)
        folder = self._folder(job_id)
        if any(entry.name != META_FILE for entry in folder.iterdir()):
            raise FileExistsError(f'Job "{job_id}" already has outputs.')
        for report_format, paths in outcome.files.items():
            for path in paths:
                (folder / report_format.value).mkdir(exist_ok=True)
                shutil.move(path, folder / report_format.value / path.name)
        for report_format, paths in outcome.files.items():
            if len(paths) > 1:
                _zip(folder / report_format.value, _format_zip(folder, report_format), ["."])
        _zip(folder, folder / REPORT_ZIP, folder_names=[f.value for f in outcome.formats])
        self._write(dataclasses.replace(record, formats=outcome.formats))

    def discard_outputs(self, job_id: str) -> None:
        record = self.get(job_id)
        for entry in self._folder(job_id).iterdir():
            if entry.name != META_FILE:
                shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
        self._write(dataclasses.replace(record, formats=()))

    def file_for(self, job_id: str, report_format: ReportFormat) -> Path:
        self.get(job_id)
        folder = self._folder(job_id)
        if report_format is ReportFormat.ZIP:
            if not (folder / REPORT_ZIP).is_file():
                raise FormatNotAvailable(job_id, report_format)
            return folder / REPORT_ZIP
        files = sorted(p for p in (folder / report_format.value).glob("*") if p.is_file())
        if not files:
            raise FormatNotAvailable(job_id, report_format)
        if len(files) == 1:
            return files[0]
        return _format_zip(folder, report_format)

    def delete(self, job_id: str) -> None:
        self.get(job_id)
        shutil.rmtree(self._folder(job_id))

    def delete_all(self) -> None:
        if self.reports_folder.is_dir():
            for entry in self.reports_folder.iterdir():
                if entry.is_dir():
                    shutil.rmtree(entry)
