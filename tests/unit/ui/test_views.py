"""The UI pages, with a fake API behind the app: what they show and what they flash."""

from io import BytesIO

import pytest
from bs4 import BeautifulSoup
from werkzeug.datastructures import FileStorage

from fingerprinter.entrypoints.ui import create_app

ERROR_CARD = {"class": "card red lighten-3"}
SUCCESS_CARD = {"class": "card blue lighten-3"}


class FakeResponse:
    def __init__(self, status_code=200, payload=None, content=b"", headers=None):
        self.status_code = status_code
        self._payload = payload
        self.content = content
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeApi:
    """Answers each client call with a canned response and remembers what was asked."""

    def __init__(self) -> None:
        self.answers: dict[str, FakeResponse] = {}
        self.calls: list[tuple] = []

    def _answer(self, name: str, *args) -> FakeResponse:
        self.calls.append((name, *args))
        return self.answers.get(name, FakeResponse(200, []))

    def fingerprint_sparql_endpoint(self, url, graphs):
        return self._answer("fingerprint_sparql_endpoint", url, graphs)

    def fingerprint_file(self, data_file):
        return self._answer("fingerprint_file", data_file.filename)

    def get_reports(self):
        return self._answer("get_reports")

    def get_report(self, job_id, report_format):
        return self._answer("get_report", job_id, report_format)

    def delete_report(self, job_id):
        return self._answer("delete_report", job_id)

    def get_active_tasks(self):
        return self._answer("get_active_tasks")

    def cancel_task(self, task_id):
        return self._answer("cancel_task", task_id)


@pytest.fixture
def api() -> FakeApi:
    return FakeApi()


@pytest.fixture
def client(api):
    app = create_app("http://api.test", "ui-secret")
    app.config["WTF_CSRF_ENABLED"] = False
    app.extensions["api"] = api
    return app.test_client()


def page(response) -> BeautifulSoup:
    return BeautifulSoup(response.data, "html.parser")


FORMATS = ["html", "json", "shacl", "puml", "pattern", "shex", "pitfalls"]


def record(job_id="job-1", state="completed", **fields):
    return {
        "id": job_id,
        "source": {"endpoint": "http://e/sparql", "graphs": []},
        "created_at": "2026-11-08T10:00:00+00:00",
        "state": state,
        "reason": None,
        "failures": [],
        "formats": FORMATS,
        **fields,
    }


def problem(status, **fields):
    return FakeResponse(status, {"status": status, **fields})


def test_the_app_needs_the_secret_key_it_is_given():
    assert create_app("http://api.test", "ui-secret").config["SECRET_KEY"] == "ui-secret"


def test_failures_are_shown(client, api):
    api.answers["get_reports"] = FakeResponse(
        200,
        [
            record("ok"),
            record("partial", "completed_with_failures", failures=["m1 failed", "m2 failed"]),
            record("bad", "failed", reason="endpoint unreachable", formats=[]),
        ],
    )

    soup = page(client.get("/"))

    assert "Fingerprinting reports" in soup.find(id="title").get_text()
    assert soup.find(id="state-ok").get_text(strip=True) == "completed"
    assert soup.find(id="state-partial").get_text(strip=True) == "completed_with_failures"
    assert [li.get_text() for li in soup.find(id="failures-partial").find_all("li")] == [
        "m1 failed",
        "m2 failed",
    ]
    assert "endpoint unreachable" in soup.find(id="reason-bad").get_text()


def test_the_report_page_lists_the_downloads(client, api):
    api.answers["get_reports"] = FakeResponse(
        200,
        [
            record("ok"),
            record("part", formats=["html"]),
            record("bad", "failed", reason="x", formats=[]),
        ],
    )

    soup = page(client.get("/"))

    for report_format in [*FORMATS, "zip"]:
        link = soup.find("a", id=f"get-{report_format}-ok")
        assert link["href"] == f"/reports/ok/{report_format}"
    assert soup.find("a", id="get-shacl-part") is None
    assert soup.find("a", id="get-html-bad") is None
    assert soup.find("a", id="get-zip-bad") is None
    assert soup.find("a", id="remove-bad")["href"] == "/reports/bad"


def test_an_endpoint_job_is_started_and_the_active_tasks_shown(client, api):
    api.answers["fingerprint_sparql_endpoint"] = FakeResponse(202, {"task_id": "j1"})
    data = {"sparql_endpoint_url": "http://e/sparql", "graphs": "g1 g2"}

    response = client.post("/fingerprint-sparql-endpoint", data=data, follow_redirects=True)

    assert ("fingerprint_sparql_endpoint", "http://e/sparql", ["g1", "g2"]) in api.calls
    soup = page(response)
    assert "List of active tasks" in soup.find(id="title").get_text()
    assert "fingerprinting successfully started" in soup.find("div", SUCCESS_CARD).get_text()


@pytest.mark.parametrize(
    ("answer", "message"),
    [
        (problem(400), "Enter an http or https SPARQL endpoint URL."),
        (problem(413), "The file is too large."),
        (problem(503), "The job queue is unavailable. Try again later."),
        (problem(500), "The request failed (status 500)."),
    ],
)
def test_a_refused_endpoint_job_flashes_the_matrix_message(client, api, answer, message):
    api.answers["fingerprint_sparql_endpoint"] = answer

    response = client.post("/fingerprint-sparql-endpoint", data={"sparql_endpoint_url": "x"})

    assert message in page(response).find("div", ERROR_CARD).get_text()


def test_a_file_job_is_started(client, api):
    api.answers["fingerprint_file"] = FakeResponse(202, {"task_id": "j1"})
    data = {"data_file": FileStorage(BytesIO(b"data"), "data.ttl")}

    response = client.post(
        "/fingerprint-file", data=data, content_type="multipart/form-data", follow_redirects=True
    )

    assert ("fingerprint_file", "data.ttl") in api.calls
    assert "List of active tasks" in page(response).find(id="title").get_text()


def test_an_unsupported_file_flashes_the_accepted_types(client, api):
    api.answers["fingerprint_file"] = problem(415, accepted=["rdf", "ttl"])
    data = {"data_file": FileStorage(BytesIO(b"data"), "data.txt")}

    response = client.post("/fingerprint-file", data=data, content_type="multipart/form-data")

    assert (
        "This file type is not supported. Accepted: rdf, ttl."
        in page(response).find("div", ERROR_CARD).get_text()
    )


@pytest.mark.parametrize(
    ("report_format", "name", "content_type"),
    [
        ("html", "main.html", "text/html"),
        ("shacl", "shapes-x.ttl", "text/turtle"),
        ("puml", "uid-1-puml.zip", "application/zip"),
        ("zip", "report.zip", "application/zip"),
    ],
)
def test_a_download_proxies_the_api_file_with_its_name_and_type(
    client, api, report_format, name, content_type
):
    api.answers["get_report"] = FakeResponse(
        200,
        content=b"content",
        headers={"Content-Disposition": f"inline; filename={name}", "Content-Type": content_type},
    )

    response = client.get(f"/reports/uid-1/{report_format}")

    assert ("get_report", "uid-1", report_format) in api.calls
    assert response.data == b"content"
    assert response.headers["Content-Disposition"] == f"attachment; filename={name}"
    assert response.headers["Content-Type"].startswith(content_type)


def test_a_failed_download_returns_to_the_list_with_the_message(client, api):
    api.answers["get_report"] = problem(404)

    response = client.get("/reports/uid-1/shacl", follow_redirects=True)

    assert "No such job or report." in page(response).find("div", ERROR_CARD).get_text()
    assert "Fingerprinting reports" in page(response).find(id="title").get_text()


def test_a_report_is_deleted(client, api):
    api.answers["delete_report"] = FakeResponse(200, {"message": "ok"})

    response = client.get("/reports/uid-1", follow_redirects=True)

    assert ("delete_report", "uid-1") in api.calls
    assert "successfully deleted" in page(response).find("div", SUCCESS_CARD).get_text()


def test_deleting_an_unknown_report_flashes_the_message(client, api):
    api.answers["delete_report"] = problem(404)

    response = client.get("/reports/uid-1", follow_redirects=True)

    assert "No such job or report." in page(response).find("div", ERROR_CARD).get_text()


def test_the_active_tasks_are_listed_with_a_cancel_link(client, api):
    api.answers["get_active_tasks"] = FakeResponse(200, [record("task-1", "running")])

    soup = page(client.get("/tasks"))

    assert soup.find(id="state-task-1").get_text(strip=True) == "running"
    assert soup.find("a", id="stop-task-task-1")["href"] == "/revoke-task/task-1"


@pytest.mark.parametrize(
    ("answer", "card", "message"),
    [
        (FakeResponse(200, {"message": "ok"}), SUCCESS_CARD, "Job cancelled."),
        (problem(409), ERROR_CARD, "This job has already finished."),
        (problem(404), ERROR_CARD, "No such job or report."),
    ],
)
def test_cancelling_a_job_shows_the_outcome(client, api, answer, card, message):
    api.answers["cancel_task"] = answer

    response = client.get("/revoke-task/task-1", follow_redirects=True)

    assert ("cancel_task", "task-1") in api.calls
    assert message in page(response).find("div", card).get_text()
