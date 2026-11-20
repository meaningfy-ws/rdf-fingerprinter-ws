"""A stand-in for the API behind the UI: canned job records and responses, and a log of the calls."""

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup

from fingerprinter.entrypoints.ui import create_app
from fingerprinter.entrypoints.ui.api_model import ApiFile, ApiJob
from fingerprinter.entrypoints.ui.exceptions import ApiError


def problem(status: int, kind: str | None = None, **fields: Any) -> ApiError:
    """An RFC 7807 refusal as the API sends it."""
    body = {"status": status, "type": f"urn:fingerprinter:{kind}" if kind else "about:blank"}
    return ApiError(body | fields, status)


def unreachable() -> ApiError:
    return ApiError()


def served(
    name: str, content_type: str, content: bytes = b"content", chunks: Iterable[bytes] | None = None
) -> ApiFile:
    """A file the API serves; the client keeps the media type without its parameters."""
    media_type = content_type.split(";")[0]
    return ApiFile(chunks if chunks is not None else iter([content]), media_type, name)


def record(job_id: str = "job-1", state: str = "completed", **fields: Any) -> dict[str, Any]:
    """A job record as ``GET /reports`` lists it."""
    created_at = fields.pop("created_at", "2026-11-08T10:00:00+00:00")
    took = timedelta(seconds=2.4)  # every finished job took 2.4 s
    return {
        "id": job_id,
        "source": {"endpoint": "http://e/sparql", "graphs": []},
        "created_at": created_at,
        "finished_at": (datetime.fromisoformat(created_at) + took).isoformat()
        if state not in ACTIVE
        else None,
        "state": state,
        "reason": None,
        "failures": [],
        "formats": ["html", "json"] if state not in ACTIVE + ("failed", "cancelled") else [],
        "files": {},
        **fields,
    }


ACTIVE = ("queued", "running")


class FakeApi:
    """Answers each client call from ``jobs`` unless ``answers`` holds a value or an ``ApiError``."""

    def __init__(self) -> None:
        self.jobs: list[dict[str, Any]] = []
        self.answers: dict[str, Any] = {}
        self.calls: list[tuple[Any, ...]] = []

    def _answer(self, name: str, *args: Any, default: Any = None) -> Any:
        self.calls.append((name, *args))
        answer = self.answers.get(name, default)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def _parsed(self) -> list[ApiJob]:
        return [ApiJob.from_dict(job) for job in self.jobs]

    def list_jobs(self) -> list[ApiJob]:
        return self._answer("list_jobs", default=self._parsed())

    def job(self, job_id: str) -> ApiJob:
        found = next((job for job in self._parsed() if job.id == job_id), None)
        return self._answer("job", job_id, default=found or problem(404, "JobNotFound"))

    def file(self, job_id: str, report_format: str, name: str | None = None) -> ApiFile:
        args = (job_id, report_format, *([name] if name else []))
        return self._answer("file", *args, default=problem(404, "FormatNotAvailable"))

    def delete_job(self, job_id: str) -> None:
        self._answer("delete_job", job_id)

    def cancel_job(self, job_id: str) -> None:
        self._answer("cancel_job", job_id)

    def endpoint_graphs(self, url: str) -> tuple[str, ...]:
        return self._answer("endpoint_graphs", url, default=())

    def start_endpoint_job(self, url: str, graphs: list[str]) -> None:
        self._answer("start_endpoint_job", url, graphs)

    def start_file_job(self, data_file: Any) -> None:
        self._answer("start_file_job", data_file.filename)


def make_app(api: FakeApi, *, csrf: bool = False, secure_cookies: bool = False):
    app = create_app(
        "http://api.test",
        "ui-secret",
        accepted_extensions=("rdf", "ttl"),
        max_upload_bytes=2 * 1024 * 1024,
        secure_cookies=secure_cookies,
    )
    app.config["WTF_CSRF_ENABLED"] = csrf
    app.extensions["api"] = api
    return app


def page(response) -> BeautifulSoup:
    return BeautifulSoup(response.data, "html.parser")
