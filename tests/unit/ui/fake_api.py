"""A stand-in for the API behind the UI: canned job records and responses, and a log of the calls."""

from datetime import datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup

from fingerprinter.entrypoints.ui import create_app


class FakeResponse:
    """The part of ``requests.Response`` the UI reads."""

    def __init__(
        self,
        status_code: int = 200,
        payload: Any = None,
        content: bytes = b"",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.content = content
        self.headers = headers or {}

    def json(self) -> Any:
        return self._payload


def problem(status: int, kind: str | None = None, **fields: Any) -> FakeResponse:
    """An RFC 7807 answer as the API sends it."""
    body = {"status": status, "type": f"urn:fingerprinter:{kind}" if kind else "about:blank"}
    return FakeResponse(status, body | fields)


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
    """Answers each client call from ``jobs`` unless ``answers`` holds a response or an exception."""

    def __init__(self) -> None:
        self.jobs: list[dict[str, Any]] = []
        self.answers: dict[str, FakeResponse | Exception] = {}
        self.calls: list[tuple[Any, ...]] = []

    def _answer(self, name: str, *args: Any, default: FakeResponse) -> FakeResponse:
        self.calls.append((name, *args))
        answer = self.answers.get(name, default)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def get_reports(self) -> FakeResponse:
        return self._answer("get_reports", default=FakeResponse(200, self.jobs))

    def get_job(self, job_id: str) -> FakeResponse:
        found = next((job for job in self.jobs if job["id"] == job_id), None)
        default = FakeResponse(200, found) if found else problem(404, "JobNotFound")
        return self._answer("get_job", job_id, default=default)

    def get_file(self, job_id: str, report_format: str, name: str | None = None) -> FakeResponse:
        args = (job_id, report_format, *([name] if name else []))
        return self._answer("get_file", *args, default=problem(404, "FormatNotAvailable"))

    def delete_report(self, job_id: str) -> FakeResponse:
        return self._answer("delete_report", job_id, default=FakeResponse(200, {"message": "ok"}))

    def cancel_task(self, task_id: str) -> FakeResponse:
        return self._answer("cancel_task", task_id, default=FakeResponse(200, {"message": "ok"}))

    def fingerprint_sparql_endpoint(self, url: str, graphs: list[str]) -> FakeResponse:
        return self._answer(
            "fingerprint_sparql_endpoint", url, graphs, default=FakeResponse(202, {"task_id": "j1"})
        )

    def fingerprint_file(self, data_file: Any) -> FakeResponse:
        return self._answer(
            "fingerprint_file", data_file.filename, default=FakeResponse(202, {"task_id": "j1"})
        )


def make_app(api: FakeApi, *, csrf: bool = False):
    app = create_app(
        "http://api.test",
        "ui-secret",
        accepted_extensions=("rdf", "ttl"),
        max_upload_bytes=2 * 1024 * 1024,
    )
    app.config["WTF_CSRF_ENABLED"] = csrf
    app.extensions["api"] = api
    return app


def page(response) -> BeautifulSoup:
    return BeautifulSoup(response.data, "html.parser")
