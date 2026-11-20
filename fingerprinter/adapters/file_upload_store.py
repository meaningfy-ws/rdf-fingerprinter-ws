"""``UploadStore`` on the file system: ``db/<job id>/<file name>`` (design D-2)."""

import shutil
from pathlib import Path
from typing import IO

from werkzeug.utils import secure_filename

from fingerprinter.domain.exceptions import UploadTooLarge

CHUNK_BYTES = 1024 * 1024


class FileUploadStore:
    def __init__(self, upload_folder: Path, max_bytes: int):
        self.upload_folder = upload_folder
        self.max_bytes = max_bytes

    def save(self, job_id: str, stream: IO[bytes], filename: str) -> Path:
        folder = self.upload_folder / job_id
        folder.mkdir(parents=True)
        path = folder / secure_filename(filename)
        written = 0
        try:
            with path.open("wb") as target:
                while chunk := stream.read(CHUNK_BYTES):
                    written += len(chunk)
                    if written > self.max_bytes:
                        raise UploadTooLarge(filename, self.max_bytes)
                    target.write(chunk)
        except UploadTooLarge:
            self.discard(job_id)
            raise
        return path

    def discard(self, job_id: str) -> None:
        shutil.rmtree(self.upload_folder / job_id, ignore_errors=True)
