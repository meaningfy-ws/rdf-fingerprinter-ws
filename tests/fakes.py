"""In-memory fakes of the service ports (design D-2, D-11)."""

import dataclasses
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import IO

from fingerprinter.domain.exceptions import DiagramRenderFailed, FormatNotAvailable, JobNotFound
from fingerprinter.domain.model import (
    FingerprintOutcome,
    JobRecord,
    JobState,
    ReportFormat,
)
from fingerprinter.services import jobs


class JobFailed(Exception):
    """A test-only failure raised by FakeFingerprinter."""


# One file per format the library writes (the file store adds the zip itself).
_FILE_NAMES = {ReportFormat.HTML: "main.html", ReportFormat.JSON: "profile.json"}
DEFAULT_OUTCOME = FingerprintOutcome(
    files={
        report_format: (Path(_FILE_NAMES.get(report_format, f"{report_format.value}.txt")),)
        for report_format in ReportFormat
        if report_format
        not in (ReportFormat.ZIP, ReportFormat.SVG)  # made by the store / the worker
    }
)


class FakeFingerprinter:
    def __init__(self, outcome: FingerprintOutcome = DEFAULT_OUTCOME):
        self.outcome = outcome
        self.error: Exception | None = None
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def fingerprint(
        self, endpoint_url: str, graphs: tuple[str, ...], work_folder: Path
    ) -> FingerprintOutcome:
        self.calls.append((endpoint_url, graphs))
        if self.error:
            raise self.error
        # a relative path stands for a file the run wrote into its work folder: make it exist
        return FingerprintOutcome(
            files={
                report_format: tuple(self._written(path, work_folder) for path in paths)
                for report_format, paths in self.outcome.files.items()
            },
            failures=self.outcome.failures,
        )

    @staticmethod
    def _written(path: Path, work_folder: Path) -> Path:
        if path.is_absolute():
            return path
        (work_folder / path.name).write_text("@startuml\n@enduml\n")
        return work_folder / path.name


class FakeDiagramRenderer:
    """Draws every text as a one-line SVG; ``error`` makes it fail, ``fail_for`` fails some texts."""

    def __init__(self) -> None:
        self.rendered: list[str] = []
        self.error: DiagramRenderFailed | None = None
        self.fail_for: set[str] = set()

    def render(self, puml_text: str) -> bytes:
        self.rendered.append(puml_text)
        if self.error or puml_text in self.fail_for:
            raise self.error or DiagramRenderFailed("the PlantUML server refused the diagram")
        return f"<svg>{puml_text}</svg>".encode()


class FakeDatasetStore:
    def __init__(self, job_store: "InMemoryJobStore | None" = None) -> None:
        self.datasets: dict[str, Path | None] = {}
        self.actions: list[tuple[str, str]] = []
        self.fail_on_create: Exception | None = None
        self.job_store = job_store
        # the state of the dataset's job when the dataset was deleted (needs a job store)
        self.state_at_delete: dict[str, JobState] = {}

    def create(self, name: str) -> None:
        self.actions.append(("create", name))
        if self.fail_on_create:
            raise self.fail_on_create
        self.datasets[name] = None

    def load_file(self, name: str, path: Path) -> None:
        self.actions.append(("load_file", name))
        self.datasets[name] = path

    def delete(self, name: str) -> None:
        self.actions.append(("delete", name))
        if self.job_store:
            self.state_at_delete[name] = next(
                record.state
                for record in self.job_store.list()
                if jobs.dataset_name(record.id) == name
            )
        self.datasets.pop(name, None)

    def sparql_url(self, name: str) -> str:
        return f"http://fuseki.test/{name}/sparql"


class InMemoryJobStore:
    def __init__(self, clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self.clock = clock
        self.records: dict[str, JobRecord] = {}
        self.outputs: dict[str, dict[ReportFormat, tuple[Path, ...]]] = {}

    def create(self, record: JobRecord) -> None:
        self.records[record.id] = record

    def get(self, job_id: str) -> JobRecord:
        try:
            return self.records[job_id]
        except KeyError:
            raise JobNotFound(job_id) from None

    def list(self) -> list[JobRecord]:
        return list(self.records.values())

    def set_state(
        self,
        job_id: str,
        state: JobState,
        reason: str | None = None,
        failures: tuple[str, ...] = (),
    ) -> None:
        self.records[job_id] = self.get(job_id).with_state(state, reason, failures, self.clock())

    def save_outputs(self, job_id: str, outcome: FingerprintOutcome) -> None:
        record = self.get(job_id)
        if job_id in self.outputs:
            raise FileExistsError(f'Job "{job_id}" already has outputs.')
        self.outputs[job_id] = dict(outcome.files)
        self.records[job_id] = dataclasses.replace(record, files=outcome.file_names)

    def discard_outputs(self, job_id: str) -> None:
        record = self.get(job_id)
        self.outputs.pop(job_id, None)
        self.records[job_id] = dataclasses.replace(record, files={})

    def file_for(self, job_id: str, report_format: ReportFormat, name: str | None = None) -> Path:
        self.get(job_id)
        files = self.outputs.get(job_id, {}).get(report_format, ())
        if name is not None:
            files = tuple(path for path in files if path.name == name)
        if not files:
            raise FormatNotAvailable(job_id, report_format)
        return files[0]

    def delete(self, job_id: str) -> None:
        self.get(job_id)
        del self.records[job_id]
        self.outputs.pop(job_id, None)

    def delete_all(self) -> None:
        self.records.clear()
        self.outputs.clear()


class FakeUploadStore:
    def __init__(self) -> None:
        self.saved: dict[str, Path] = {}
        self.error: Exception | None = None

    def save(self, job_id: str, stream: IO[bytes], filename: str) -> Path:
        if self.error:
            raise self.error
        stream.read()
        self.saved[job_id] = Path("db") / job_id / filename
        return self.saved[job_id]

    def discard(self, job_id: str) -> None:
        self.saved.pop(job_id, None)


class FakeJobQueue:
    def __init__(self) -> None:
        self.submitted: list[tuple[str, ...]] = []
        self.cancelled: list[str] = []
        self.error: Exception | None = None

    def submit_endpoint(self, job_id: str, url: str, graphs: tuple[str, ...]) -> None:
        if self.error:
            raise self.error
        self.submitted.append((job_id, url))

    def submit_file(self, job_id: str, path: Path) -> None:
        if self.error:
            raise self.error
        self.submitted.append((job_id, str(path)))

    def cancel(self, job_id: str) -> None:
        self.cancelled.append(job_id)
