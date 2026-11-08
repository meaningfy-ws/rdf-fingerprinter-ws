"""The feature tier's stand-in for a client: it drives the services through the fakes.

There is no Flask and no HTTP here. ``attempt`` records the status the API would answer for a
service outcome or domain exception, per design D-4 and the Error matrix.
"""

import io
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fingerprinter.domain.exceptions import (
    FormatNotAvailable,
    InvalidSource,
    JobNotCancellable,
    JobNotFound,
    QueueUnavailable,
    UnsupportedFileType,
)
from fingerprinter.domain.model import ReportFormat
from fingerprinter.services import jobs, reports
from tests.fakes import (
    FakeDatasetStore,
    FakeFingerprinter,
    FakeJobQueue,
    FakeUploadStore,
    InMemoryJobStore,
)

RESOURCES = Path(__file__).parent.parent / "resources"
# The keys of config.INPUT_MIME_TYPES, which bootstrap passes to the real services.
SUPPORTED_EXTENSIONS = frozenset({"rdf", "trix", "nq", "nt", "jsonld", "n3", "ttl"})
STATUS_BY_ERROR: dict[type[Exception], int] = {
    InvalidSource: 400,
    UnsupportedFileType: 415,
    JobNotFound: 404,
    FormatNotAvailable: 404,
    JobNotCancellable: 409,
    QueueUnavailable: 503,
}
FILE_CONTENT = {"notes.txt": b"just some notes"}


class World:
    def __init__(self) -> None:
        self.store = InMemoryJobStore()
        self.queue = FakeJobQueue()
        self.uploads = FakeUploadStore()
        self.datasets = FakeDatasetStore()
        self.library = FakeFingerprinter()
        self.job_id: str | None = None
        self.status: int | None = None
        self.problem: Exception | None = None
        self.result: Any = None

    def attempt(self, ok_status: int, call: Callable[[], Any]) -> Any:
        """Run a service call; record the status the API answers and any problem."""
        self.status, self.problem, self.result = ok_status, None, None
        try:
            self.result = call()
        except tuple(STATUS_BY_ERROR) as error:
            self.status, self.problem = STATUS_BY_ERROR[type(error)], error
        return self.result

    def submit_endpoint(self, url: str) -> str | None:
        self.job_id = self.attempt(
            202, lambda: jobs.submit_endpoint_job(url, (), jobs=self.store, queue=self.queue)
        )
        return self.job_id

    def upload(self, filename: str) -> str | None:
        content = FILE_CONTENT.get(filename) or (RESOURCES / filename).read_bytes()
        self.job_id = self.attempt(
            202,
            lambda: jobs.submit_file_job(
                io.BytesIO(content),
                filename,
                supported_extensions=SUPPORTED_EXTENSIONS,
                jobs=self.store,
                uploads=self.uploads,
                queue=self.queue,
            ),
        )
        return self.job_id

    def run_endpoint(self, job_id: str, url: str) -> None:
        jobs.run_endpoint_job(job_id, url, (), jobs=self.store, fingerprinter=self.library)

    def run_file(self, job_id: str) -> None:
        jobs.run_file_job(
            job_id,
            self.uploads.saved[job_id],
            jobs=self.store,
            datasets=self.datasets,
            uploads=self.uploads,
            fingerprinter=self.library,
        )

    def status_of(self, job_id: str):
        return self.attempt(200, lambda: jobs.job_status(job_id, jobs=self.store))

    def cancel(self, job_id: str) -> None:
        self.attempt(
            200,
            lambda: jobs.cancel_job(
                job_id, jobs=self.store, queue=self.queue, uploads=self.uploads
            ),
        )

    def list_reports(self) -> list:
        return self.attempt(200, lambda: reports.list_reports(jobs=self.store))

    def download(self, job_id: str, format_name: str) -> None:
        try:
            report_format = ReportFormat(format_name)
        except ValueError as error:  # Connexion's enum validation answers 400 before any handler
            self.status, self.problem, self.result = 400, error, None
            return
        self.attempt(200, lambda: reports.report_download(job_id, report_format, jobs=self.store))

    def delete(self, job_id: str) -> None:
        self.attempt(200, lambda: reports.delete_report(job_id, jobs=self.store))

    def delete_all(self) -> None:
        self.attempt(200, lambda: reports.delete_all_reports(jobs=self.store))
