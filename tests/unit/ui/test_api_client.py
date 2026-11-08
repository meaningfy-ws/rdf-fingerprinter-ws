"""The UI's HTTP client of the API: each call reaches the right route with the right payload."""

from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from fingerprinter.entrypoints.ui.api_wrapper import REQUEST_TIMEOUT_SECONDS, ApiClient

API = "http://api.test:4020"


class RecordingRequests:
    """Stands in for ``requests``: records each call and answers with a marker."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    def __getattr__(self, method: str):
        def call(url: str, **kwargs: object) -> str:
            self.calls.append((method, url, kwargs))
            return f"{method} answer"

        return call


@pytest.fixture
def requests_double(monkeypatch) -> RecordingRequests:
    double = RecordingRequests()
    monkeypatch.setattr("fingerprinter.entrypoints.ui.api_wrapper.requests", double)
    return double


@pytest.fixture
def client() -> ApiClient:
    return ApiClient(f"{API}/")


def test_an_endpoint_job_posts_the_url_and_the_graphs(client, requests_double):
    answer = client.fingerprint_sparql_endpoint("http://e/sparql", ["http://g"])

    assert answer == "post answer"
    assert requests_double.calls == [
        (
            "post",
            f"{API}/fingerprint-sparql-endpoint",
            {
                "json": {"sparql_endpoint_url": "http://e/sparql", "graphs": ["http://g"]},
                "timeout": REQUEST_TIMEOUT_SECONDS,
            },
        )
    ]


def test_an_endpoint_job_without_graphs_sends_none(client, requests_double):
    client.fingerprint_sparql_endpoint("http://e/sparql", [])

    assert requests_double.calls[0][2]["json"] == {"sparql_endpoint_url": "http://e/sparql"}


def test_a_file_job_posts_the_file_as_multipart(client, requests_double):
    upload = FileStorage(BytesIO(b"data"), "data.ttl", content_type="text/turtle")

    client.fingerprint_file(upload)

    method, url, kwargs = requests_double.calls[0]
    assert (method, url) == ("post", f"{API}/fingerprint-file")
    assert kwargs["files"]["data_file"] == ("data.ttl", upload.stream, "text/turtle")


@pytest.mark.parametrize(
    ("call", "path"),
    [
        (lambda c: c.get_report("../x?y#z", "h/tml"), "/reports/..%2Fx%3Fy%23z/h%2Ftml"),
        (lambda c: c.delete_report("a/b"), "/reports/a%2Fb"),
        (lambda c: c.cancel_task("a b"), "/tasks/a%20b"),
    ],
)
def test_path_values_are_quoted_so_they_stay_one_segment(client, requests_double, call, path):
    call(client)

    assert requests_double.calls[0][1] == f"{API}{path}"


@pytest.mark.parametrize(
    ("call", "method", "path"),
    [
        (lambda c: c.get_reports(), "get", "/reports"),
        (lambda c: c.get_report("j1", "html"), "get", "/reports/j1/html"),
        (lambda c: c.delete_report("j1"), "delete", "/reports/j1"),
        (lambda c: c.get_active_tasks(), "get", "/tasks/active"),
        (lambda c: c.cancel_task("j1"), "delete", "/tasks/j1"),
    ],
)
def test_each_call_reaches_its_route(client, requests_double, call, method, path):
    answer = call(client)

    assert answer == f"{method} answer"
    assert requests_double.calls == [(method, f"{API}{path}", {"timeout": REQUEST_TIMEOUT_SECONDS})]
