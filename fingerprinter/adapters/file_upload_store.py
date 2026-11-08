"""``UploadStore`` on the file system: ``db/<job id>/<file name>`` (design D-2)."""

import shutil
from pathlib import Path
from typing import BinaryIO

from werkzeug.utils import secure_filename


class FileUploadStore:
    def __init__(self, upload_folder: Path):
        self.upload_folder = upload_folder

    def save(self, job_id: str, stream: BinaryIO, filename: str) -> Path:
        folder = self.upload_folder / job_id
        folder.mkdir(parents=True)
        path = folder / secure_filename(filename)
        with path.open("wb") as target:
            shutil.copyfileobj(stream, target)
        return path

    def discard(self, job_id: str) -> None:
        shutil.rmtree(self.upload_folder / job_id, ignore_errors=True)
