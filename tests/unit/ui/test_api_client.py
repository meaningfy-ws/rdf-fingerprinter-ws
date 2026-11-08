"""The UI's HTTP client of the API: each call reaches the right route and answers typed values."""

from datetime import UTC, datetime
from io import BytesIO
from typing import Any

import pytest
import requests
from werkzeug.datastructures import FileStorage

from fingerprinter.entrypoints.ui.api_client import REQUEST_TIMEOUT_SECONDS, ApiClient
from fingerprinter.entrypoints.ui.api_model import ApiJob, ApiState
from fingerprinter.entrypoints.ui.exceptions import ApiError
from tests.unit.ui.fake_api import record

API = "http://api.test:4020"


class Answer:
    """The part of ``requests.Response`` the client reads."""

    def __init__(self, status: int = 200, body: Any = None, *, headers=None, chunks=(b"",)):
        self.status_code = status
        self.body = body
        self.headers = headers or {}
        self.chunks = chunks
        self.closed = False

    def json(self) -> Any:
        if self.body is ValueError:
            raise ValueError("not json")
        return self.body

    def iter_content(self, size: int):
        return iter(self.chunks)

    def close(self) -> None:
        self.closed = True


class RecordingRequests:
    """Stands in for ``requests``: records each call and answers with ``answer`` (or raises it)."""

    RequestException = requests.RequestException

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.answer: Any = Answer()

    def request(self, method: str, url: str, **kwargs: Any) -> Answer:
        self.calls.append((method, url, kwargs))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


@pytest.fixture
def requests_double(monkeypatch) -> RecordingRequests:
    double = RecordingRequests()
    monkeypatch.setattr("fingerprinter.entrypoints.ui.api_client.requests", double)
    return double


@pytest.fixture
def client() -> ApiClient:
    return ApiClient(f"{API}/")


def test_an_endpoint_job_posts_the_url_and_the_graphs(client, requests_double):
    client.start_endpoint_job("http://e/sparql", ["http://g"])

    assert requests_double.calls == [
        (
            "POST",
            f"{API}/fingerprint-sparql-endpoint",
            {
                "json": {"sparql_endpoint_url": "http://e/sparql", "graphs": ["http://g"]},
                "timeout": REQUEST_TIMEOUT_SECONDS,
            },
        )
    ]


def test_an_endpoint_job_without_graphs_sends_none(client, requests_double):
    client.start_endpoint_job("http://e/sparql", [])

    assert requests_double.calls[0][2]["json"] == {"sparql_endpoint_url": "http://e/sparql"}


def test_the_graphs_of_an_endpoint_are_asked_with_the_url_as_a_query_value(client, requests_double):
    requests_double.answer = Answer(200, {"graphs": ["http://g/1", "http://g/2"]})

    graphs = client.endpoint_graphs("http://e/sparql?a=b")

    assert graphs == ("http://g/1", "http://g/2")
    assert requests_double.calls == [
        (
            "GET",
            f"{API}/endpoint-graphs",
            {"params": {"url": "http://e/sparql?a=b"}, "timeout": REQUEST_TIMEOUT_SECONDS},
        )
    ]
    assert REQUEST_TIMEOUT_SECONDS == 60


@pytest.mark.parametrize("body", [{"no": "graphs"}, ["g"], {"graphs": 7}, ValueError])
def test_a_graph_listing_that_is_not_one_is_a_server_error(client, requests_double, body):
    requests_double.answer = Answer(200, body)

    with pytest.raises(ApiError) as error:
        client.endpoint_graphs("http://e/sparql")

    assert error.value.status == 502


def test_a_file_job_posts_the_file_as_multipart(client, requests_double):
    upload = FileStorage(BytesIO(b"data"), "data.ttl", content_type="text/turtle")

    client.start_file_job(upload)

    method, url, kwargs = requests_double.calls[0]
    assert (method, url) == ("POST", f"{API}/fingerprint-file")
    assert kwargs["files"]["data_file"] == ("data.ttl", upload.stream, "text/turtle")


@pytest.mark.parametrize(
    ("call", "path"),
    [
        (lambda c: c.job("../x?y#z"), "/reports/..%2Fx%3Fy%23z"),
        (lambda c: c.file("../x?y#z", "h/tml"), "/reports/..%2Fx%3Fy%23z/h%2Ftml"),
        (lambda c: c.file("j1", "svg", "a/b c.svg"), "/reports/j1/svg/a%2Fb%20c.svg"),
        (lambda c: c.delete_job("a/b"), "/reports/a%2Fb"),
        (lambda c: c.cancel_job("a b"), "/tasks/a%20b"),
    ],
)
def test_path_values_are_quoted_so_they_stay_one_segment(client, requests_double, call, path):
    requests_double.answer = Answer(200, record("j1"))

    call(client)

    assert requests_double.calls[0][1] == f"{API}{path}"


@pytest.mark.parametrize(
    ("call", "method", "path"),
    [
        (lambda c: c.list_jobs(), "GET", "/reports"),
        (lambda c: c.job("j1"), "GET", "/reports/j1"),
        (lambda c: c.file("j1", "html"), "GET", "/reports/j1/html"),
        (lambda c: c.file("j1", "svg", "d.svg"), "GET", "/reports/j1/svg/d.svg"),
        (lambda c: c.delete_job("j1"), "DELETE", "/reports/j1"),
        (lambda c: c.cancel_job("j1"), "DELETE", "/tasks/j1"),
    ],
)
def test_each_call_reaches_its_route(client, requests_double, call, method, path):
    requests_double.answer = Answer(200, [] if path == "/reports" else record("j1"))

    call(client)

    ((sent_method, url, kwargs),) = requests_double.calls
    assert (sent_method, url) == (method, f"{API}{path}")
    assert kwargs["timeout"] == REQUEST_TIMEOUT_SECONDS


# --- what the answers become ---------------------------------------------------------------------


def test_the_jobs_are_parsed_into_typed_values(client, requests_double):
    requests_double.answer = Answer(200, [record("j1", "completed", failures=["m"])])

    (job,) = client.list_jobs()

    assert job == ApiJob(
        id="j1",
        created_at=datetime(2026, 11, 8, 10, 0, tzinfo=UTC),
        state=ApiState.COMPLETED,
        endpoint="http://e/sparql",
        failures=("m",),
        finished_at=datetime(2026, 11, 8, 10, 0, 2, 400000, tzinfo=UTC),
    )
    assert job.source_name == "http://e/sparql"


def test_the_files_of_a_job_are_listed_per_format(client, requests_double):
    files = {"html": ["main.html"], "svg": ["diagram-a.svg", "diagram-b.svg"]}
    requests_double.answer = Answer(200, [record("j1", "completed", files=files)])

    (job,) = client.list_jobs()

    assert job.files == {"html": ("main.html",), "svg": ("diagram-a.svg", "diagram-b.svg")}


def test_a_record_with_missing_fields_takes_defaults_and_an_unknown_state_stays_raw(
    client, requests_double
):
    requests_double.answer = Answer(
        200, [{"id": "j1", "created_at": "2026-11-08T10:00:00+00:00", "state": "on-hold"}]
    )

    (job,) = client.list_jobs()

    assert (job.state, job.graphs, job.failures, job.finished_at, job.source_name, job.files) == (
        "on-hold", (), (), None, "", {},
    )  # fmt: skip
    assert job.state not in set(ApiState)


@pytest.mark.parametrize("body", [{"not": "a list"}, [{"no": "id"}], [7], ValueError])
def test_an_answer_that_is_not_the_jobs_is_a_server_error(client, requests_double, body):
    requests_double.answer = Answer(200, body)

    with pytest.raises(ApiError) as error:
        client.list_jobs()

    assert (error.value.status, error.value.problem, error.value.unreachable) == (502, None, False)


def test_one_job_is_parsed_and_a_malformed_one_is_a_server_error(client, requests_double):
    requests_double.answer = Answer(200, record("j1", "running"))
    assert client.job("j1").state is ApiState.RUNNING

    requests_double.answer = Answer(200, {"no": "id"})
    with pytest.raises(ApiError) as error:
        client.job("j1")
    assert error.value.status == 502


# --- what the failures become --------------------------------------------------------------------


@pytest.mark.parametrize("failure", [requests.ConnectionError("down"), requests.Timeout("slow")])
def test_an_api_that_gives_no_answer_is_unreachable(client, requests_double, failure):
    requests_double.answer = failure

    with pytest.raises(ApiError) as error:
        client.delete_job("j1")

    assert error.value.unreachable
    assert (error.value.status, error.value.problem) == (None, None)


def test_a_refusal_carries_its_status_and_problem_and_is_closed(client, requests_double):
    body = {"type": "urn:fingerprinter:JobNotFound", "status": 404}
    requests_double.answer = Answer(404, body)

    with pytest.raises(ApiError) as error:
        client.job("j1")

    assert (error.value.status, error.value.problem) == (404, body)
    assert not error.value.unreachable
    assert requests_double.answer.closed


@pytest.mark.parametrize("body", [ValueError, ["a list"], None])
def test_a_refusal_without_a_problem_body_has_no_problem(client, requests_double, body):
    requests_double.answer = Answer(502, body)

    with pytest.raises(ApiError) as error:
        client.cancel_job("j1")

    assert (error.value.status, error.value.problem) == (502, None)


# --- files ---------------------------------------------------------------------------------------


def test_a_file_is_streamed_with_the_name_and_type_of_the_api(client, requests_double):
    requests_double.answer = Answer(
        200,
        headers={
            "Content-Type": "application/zip",
            "Content-Disposition": "attachment; filename=report.zip",
        },
        chunks=(b"ab", b"cd"),
    )

    file = client.file("j1", "zip")

    assert requests_double.calls[0][2]["stream"] is True
    assert (file.mimetype, file.filename) == ("application/zip", "report.zip")
    assert not requests_double.answer.closed  # nothing is read before it is asked for
    assert list(file.chunks) == [b"ab", b"cd"]
    assert requests_double.answer.closed


def test_a_file_without_headers_has_no_name_or_type(client, requests_double):
    requests_double.answer = Answer(200)

    file = client.file("j1", "zip")

    assert (file.mimetype, file.filename) == (None, None)


@pytest.mark.parametrize("gone", ["get_report", "get_active_tasks", "get_reports", "get_file"])
def test_the_calls_nothing_uses_any_more_are_gone(client, gone):
    assert not hasattr(client, gone)
