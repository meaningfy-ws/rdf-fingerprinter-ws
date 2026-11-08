"""The UI's HTTP client of the API: each call reaches the right route and returns the API's answer."""

from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from fingerprinter.config import config
from fingerprinter.entrypoints.ui import api_wrapper

API = config.RDF_FINGERPRINTER_API_SERVICE


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: object = None, content: bytes = b"body"):
        self.status_code = status_code
        self._payload = payload
        self.content = content

    def json(self) -> object:
        return self._payload


class RecordingRequests:
    """Stands in for ``requests``: records each call and answers with one fixed response."""

    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls: list[tuple[str, str, dict]] = []

    def _record(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        return self.response

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        return self._record("GET", url, **kwargs)

    def post(self, url: str, **kwargs: object) -> FakeResponse:
        return self._record("POST", url, **kwargs)

    def delete(self, url: str, **kwargs: object) -> FakeResponse:
        return self._record("DELETE", url, **kwargs)


@pytest.fixture
def fake_requests(monkeypatch: pytest.MonkeyPatch) -> RecordingRequests:
    fake = RecordingRequests(FakeResponse(payload={"ok": True}))
    monkeypatch.setattr(api_wrapper, "requests", fake)
    return fake


def test_endpoint_job_sends_the_graphs_only_when_given(fake_requests: RecordingRequests) -> None:
    api_wrapper.fingerprint_sparql_endpoint("http://example.org/sparql", graphs=[])
    api_wrapper.fingerprint_sparql_endpoint(
        "http://example.org/sparql", graphs=["http://ex.org/g1"]
    )

    (_, url, first), (_, _, second) = fake_requests.calls
    assert url == f"{API}/fingerprint-sparql-endpoint"
    assert first["json"] == {"sparql_endpoint_url": "http://example.org/sparql"}
    assert second["json"]["graphs"] == ["http://ex.org/g1"]


def test_file_job_uploads_the_file(fake_requests: RecordingRequests) -> None:
    data_file = FileStorage(BytesIO(b"<a> <b> <c> ."), "data.ttl", content_type="text/turtle")

    content, status = api_wrapper.fingerprint_file(data_file)

    method, url, kwargs = fake_requests.calls[0]
    assert (method, url, status, content) == ("POST", f"{API}/fingerprint-file", 200, b"body")
    assert kwargs["files"]["data_file"][0] == "data.ttl"


@pytest.mark.parametrize(
    ("call", "method", "path"),
    [
        (lambda: api_wrapper.get_fingerprintings(), "GET", "/reports"),
        (lambda: api_wrapper.delete_fingerprinting("uid-1"), "DELETE", "/reports/uid-1"),
        (lambda: api_wrapper.get_active_tasks(), "GET", "/tasks/active"),
    ],
)
def test_json_calls_return_the_payload_and_status(
    fake_requests: RecordingRequests, call, method: str, path: str
) -> None:
    payload, status = call()

    assert fake_requests.calls[0][:2] == (method, f"{API}{path}")
    assert (payload, status) == ({"ok": True}, 200)


def test_report_download_asks_for_the_report_type(fake_requests: RecordingRequests) -> None:
    content, status = api_wrapper.get_report("uid-1", "zip")

    method, url, kwargs = fake_requests.calls[0]
    assert (method, url, kwargs["params"]) == (
        "GET",
        f"{API}/reports/uid-1",
        {"report_type": "zip"},
    )
    assert (content, status) == (b"body", 200)


def test_revoke_task_deletes_the_task(fake_requests: RecordingRequests) -> None:
    content, status = api_wrapper.revoke_task("task-1")

    assert fake_requests.calls[0][:2] == ("DELETE", f"{API}/tasks/task-1")
    assert (content, status) == (b"body", 200)
