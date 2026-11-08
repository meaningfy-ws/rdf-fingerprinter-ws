"""The feature tier's stand-in for a client: it drives the API's test client over the fakes.

Requests go through ``create_app`` with the service ports faked, so status codes come from the real
error handlers and Connexion's validation. The worker side (running a job) calls the job services
directly, as the Celery tasks do.
"""

import io
from http import HTTPStatus
from pathlib import Path
from typing import Any

from fingerprinter.config import INPUT_MIME_TYPES
from fingerprinter.domain.model import FingerprintOutcome, ReportFormat
from fingerprinter.entrypoints.api import create_app
from fingerprinter.services import jobs
from fingerprinter.services.ports import Services
from tests.fakes import (
    FakeDatasetStore,
    FakeFingerprinter,
    FakeJobQueue,
    FakeUploadStore,
    InMemoryJobStore,
)

RESOURCES = Path(__file__).parent.parent / "resources"
# the file each format gets from the library (the file store adds the zip format itself)
LIBRARY_FILE_NAMES = {
    ReportFormat.HTML: "main.html",
    ReportFormat.JSON: "profile.json",
    ReportFormat.SHACL: "shapes-x.ttl",
    ReportFormat.PUML: "diagram-x.puml",
    ReportFormat.PATTERN: "patterns-x.md",
    ReportFormat.SHEX: "shex-x.shex",
    ReportFormat.PITFALLS: "pitfalls-x.tsv",
}
FILE_CONTENT = {"notes.txt": b"just some notes"}


class World:
    def __init__(self, folder: Path) -> None:
        self.store = InMemoryJobStore()
        self.queue = FakeJobQueue()
        self.uploads = FakeUploadStore()
        self.datasets = FakeDatasetStore()
        self.library = FakeFingerprinter(self._outcome(folder))
        self.client = create_app(
            Services(
                job_store=self.store,
                upload_store=self.uploads,
                queue=self.queue,
                dataset_store=self.datasets,
                fingerprinter=self.library,
                supported_extensions=frozenset(INPUT_MIME_TYPES),
            )
        ).test_client()
        self.job_id: str | None = None
        self.status: int | None = None
        self.problem: dict[str, Any] | None = None
        self.result: Any = None
        self.response: Any = None

    @staticmethod
    def _outcome(folder: Path) -> FingerprintOutcome:
        """The files a run writes (one per format), which exist so that a download can serve them."""
        files = {}
        for report_format, name in LIBRARY_FILE_NAMES.items():
            path = folder / name
            path.write_text("content")
            files[report_format] = (path,)
        return FingerprintOutcome(files=files)

    def respond(self, response: Any) -> Any:
        """Record the API's answer: its status, its problem if any, else its JSON body."""
        self.status = response.status_code
        failed = response.status_code >= HTTPStatus.BAD_REQUEST
        self.problem = response.json() if failed else None
        is_json = response.headers["content-type"].startswith("application/json")
        self.result = response.json() if is_json and not failed else None
        self.response = response
        return self.result

    def submit_endpoint(self, url: str) -> str | None:
        body = self.respond(
            self.client.post("/fingerprint-sparql-endpoint", json={"sparql_endpoint_url": url})
        )
        self.job_id = body["task_id"] if body else None
        return self.job_id

    def upload(self, filename: str) -> str | None:
        content = FILE_CONTENT.get(filename) or (RESOURCES / filename).read_bytes()
        files = {"data_file": (filename, io.BytesIO(content))}
        body = self.respond(self.client.post("/fingerprint-file", files=files))
        self.job_id = body["task_id"] if body else None
        return self.job_id

    def run_endpoint(self, job_id: str, url: str) -> None:
        jobs.run_endpoint_job(job_id, url, (), job_store=self.store, fingerprinter=self.library)

    def run_file(self, job_id: str) -> None:
        jobs.run_file_job(
            job_id,
            self.uploads.saved[job_id],
            job_store=self.store,
            dataset_store=self.datasets,
            upload_store=self.uploads,
            fingerprinter=self.library,
        )

    def status_of(self, job_id: str) -> Any:
        return self.respond(self.client.get(f"/tasks/{job_id}"))

    def cancel(self, job_id: str) -> None:
        self.respond(self.client.delete(f"/tasks/{job_id}"))

    def list_reports(self) -> Any:
        return self.respond(self.client.get("/reports"))

    def download(self, job_id: str, format_name: str) -> None:
        self.respond(self.client.get(f"/reports/{job_id}/{format_name}"))

    def delete(self, job_id: str) -> None:
        self.respond(self.client.delete(f"/reports/{job_id}"))

    def delete_all(self) -> None:
        self.respond(self.client.delete("/remove-reports"))
