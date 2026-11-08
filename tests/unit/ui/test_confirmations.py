"""Delete, cancel, downloads and the report: the job-console scenarios on acting on a job."""

from urllib.parse import quote

import pytest
import requests

from tests.unit.ui.fake_api import FakeResponse, make_app, page, problem, record

NOT_FOUND = "No such job or report."


def flash_of(response, kind):
    return page(response).find(class_=f"flash-{kind}").get_text(strip=True)


# --- the confirmation pages -------------------------------------------------------------------------


def test_the_delete_confirmation_names_the_job_and_focuses_keep_it_first(client, api):
    api.jobs = [record("j1", "completed", source={"file": "treaties.rdf", "graphs": []})]

    soup = page(client.get("/jobs/j1/delete?next=/"))

    dialog = soup.find(attrs={"role": "alertdialog"})
    assert dialog.find("h1").text == "Delete this report?"
    assert "treaties.rdf" in dialog.text
    assert "This cannot be undone." in dialog.text
    assert dialog["aria-labelledby"] == "dialog-title"
    controls = dialog.find_all(["a", "button"])
    assert [c.get_text(strip=True) for c in controls] == ["Keep it", "Delete report"]
    assert controls[0].has_attr("autofocus")
    assert controls[0]["href"] == "/"
    form = dialog.find("form")
    assert form["method"] == "post"
    assert form["action"].startswith("/jobs/j1/delete?")


def test_the_cancel_confirmation_follows_the_same_pattern(client, api):
    api.jobs = [record("j1", "running", source={"file": "treaties.rdf", "graphs": []})]

    dialog = page(client.get("/jobs/j1/cancel?next=/")).find(attrs={"role": "alertdialog"})

    assert dialog.find("h1").text == "Cancel this job?"
    assert "treaties.rdf" in dialog.text
    assert [c.get_text(strip=True) for c in dialog.find_all(["a", "button"])] == [
        "Keep it",
        "Cancel job",
    ]


@pytest.mark.parametrize("action", ["delete", "cancel"])
def test_a_confirmation_for_an_unknown_job_is_the_not_found_page(client, api, action):
    response = client.get(f"/jobs/nope/{action}")

    assert response.status_code == 404
    soup = page(response)
    assert soup.find("h1").text == "Not found"
    assert NOT_FOUND in soup.find("main").text
    assert soup.find("main").find("a")["href"] == "/"


@pytest.mark.parametrize(
    ("next_url", "kept"),
    [
        ("/jobs/abc", "/jobs/abc"),
        ("/?show=active", "/?show=active"),
        ("https://evil.example/x", "/"),
        ("//evil.example/x", "/"),
        ("/\\evil.example", "/"),
        ("javascript:alert(1)", "/"),
        ("jobs/abc", "/"),
        ("", "/"),
    ],
)
def test_next_must_be_a_local_path(client, api, next_url, kept):
    api.jobs = [record("j1")]

    dialog = page(client.get("/jobs/j1/delete", query_string={"next": next_url}))

    assert dialog.find("a", string="Keep it")["href"] == kept


# --- A delete is abandoned -------------------------------------------------------------------------


def test_a_delete_is_abandoned(client, api):
    api.jobs = [record("j1", "completed")]
    dialog = page(client.get("/jobs/j1/delete?next=/"))

    keep = client.get(dialog.find("a", string="Keep it")["href"])

    assert keep.status_code == 200
    assert page(keep).find("tbody", id="job-rows").find("tr", id="job-j1") is not None
    assert not [call for call in api.calls if call[0] == "delete_report"]


def test_a_report_is_deleted_and_the_jobs_page_says_so(client, api):
    api.jobs = [record("j1")]

    response = client.post("/jobs/j1/delete", follow_redirects=True)

    assert ("delete_report", "j1") in api.calls
    assert response.request.path == "/"
    assert flash_of(response, "success") == "Report deleted."


@pytest.mark.parametrize(
    ("answer", "sentence"),
    [
        (problem(404, "JobNotFound"), NOT_FOUND),
        (problem(409, "JobIsActive"), "Cancel the job before deleting it."),
        (requests.ConnectionError("down"), "The service is not reachable. Try again in a moment."),
    ],
)
def test_a_refused_delete_flashes_the_sentence_on_the_jobs_page(client, api, answer, sentence):
    api.answers["delete_report"] = answer

    response = client.post("/jobs/j1/delete?next=/jobs/j1", follow_redirects=True)

    assert response.request.path == "/"
    assert flash_of(response, "error") == sentence


# --- A running job is cancelled -------------------------------------------------------------------------


def test_a_running_job_is_cancelled(client, api):
    api.jobs = [record("j1", "running")]

    response = client.post("/jobs/j1/cancel?next=/", follow_redirects=True)
    assert ("cancel_task", "j1") in api.calls
    assert flash_of(response, "success") == "Job cancelled."

    api.jobs = [record("j1", "cancelled")]
    row = page(client.get("/")).find("tr", id="job-j1")
    assert row.find(class_="badge").text == "Cancelled"


def test_cancelling_returns_to_the_page_it_came_from(client, api):
    response = client.post("/jobs/j1/cancel?next=/%3Fshow%3Dactive")

    assert response.headers["Location"] == "/?show=active"


def test_cancelling_never_redirects_away_from_the_site(client, api):
    response = client.post("/jobs/j1/cancel", query_string={"next": "https://evil.example"})

    assert response.headers["Location"] == "/"


# --- A finished job offers no cancel -------------------------------------------------------------------


@pytest.mark.parametrize("state", ["completed", "completed_with_failures", "failed", "cancelled"])
def test_a_finished_job_offers_no_cancel(client, api, state):
    api.jobs = [record("j1", state)]

    soup = page(client.get("/"))

    assert not [a for a in soup.find_all("a") if "/cancel" in a["href"]]
    assert "Cancel job…" not in soup.text


def test_cancelling_a_finished_job_says_it_has_already_finished(client, api):
    api.answers["cancel_task"] = problem(409, "JobNotCancellable")

    response = client.post("/jobs/j1/cancel?next=/", follow_redirects=True)

    assert flash_of(response, "error") == "This job has already finished."


def test_cancelling_an_unknown_job_is_not_found(client, api):
    api.answers["cancel_task"] = problem(404, "JobNotFound")

    response = client.post("/jobs/j1/cancel?next=/", follow_redirects=True)

    assert flash_of(response, "error") == NOT_FOUND


def test_a_delete_or_cancel_without_the_csrf_token_is_refused(api):
    client = make_app(api, csrf=True).test_client()

    assert client.post("/jobs/j1/delete").status_code == 400
    assert client.post("/jobs/j1/cancel").status_code == 400
    assert api.calls == []


def test_the_confirmation_form_carries_a_csrf_token(api):
    api.jobs = [record("j1")]
    client = make_app(api, csrf=True).test_client()

    form = page(client.get("/jobs/j1/delete")).find("form")
    token = form.find("input", attrs={"name": "csrf_token"})["value"]

    assert client.post(form["action"], data={"csrf_token": token}).status_code == 302
    assert ("delete_report", "j1") in api.calls


# --- downloads --------------------------------------------------------------------------------------------


def file_answer(name, content_type, content=b"content"):
    return FakeResponse(
        200,
        content=content,
        headers={"Content-Disposition": f"inline; filename={name}", "Content-Type": content_type},
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
def test_a_download_is_an_attachment_with_the_api_name_and_type(
    client, api, report_format, name, content_type
):
    api.answers["get_file"] = file_answer(name, content_type)

    response = client.get(f"/jobs/uid-1/files/{report_format}")

    assert ("get_file", "uid-1", report_format) in api.calls
    assert response.data == b"content"
    assert response.headers["Content-Disposition"] == f"attachment; filename={name}"
    assert response.headers["Content-Type"].startswith(content_type)
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_one_file_of_a_format_is_an_attachment_too(client, api):
    api.answers["get_file"] = file_answer("diagram-x.svg", "image/svg+xml", b"<svg/>")

    response = client.get("/jobs/uid-1/files/svg/diagram-x.svg")

    assert ("get_file", "uid-1", "svg", "diagram-x.svg") in api.calls
    assert response.headers["Content-Disposition"] == "attachment; filename=diagram-x.svg"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_a_download_with_unwanted_markup_is_still_an_attachment(client, api):
    api.answers["get_file"] = file_answer("evil.html", "text/html", b"<script>alert(1)</script>")

    response = client.get("/jobs/uid-1/files/html")

    assert response.headers["Content-Disposition"].startswith("attachment")
    assert "Content-Security-Policy" not in response.headers


def test_a_download_the_api_does_not_have_is_the_not_found_page(client, api):
    api.answers["get_file"] = problem(404, "FormatNotAvailable")

    response = client.get("/jobs/uid-1/files/shacl")

    assert response.status_code == 404
    assert NOT_FOUND in page(response).find("main").text


def test_an_id_the_api_does_not_accept_is_not_found(client, api):
    api.answers["get_file"] = problem(400)

    response = client.get("/jobs/not-a-uuid/files/shacl")

    assert response.status_code == 404
    assert NOT_FOUND in page(response).find("main").text


def test_a_download_while_the_service_is_down_says_so(client, api):
    api.answers["get_file"] = requests.ConnectionError("down")

    response = client.get("/jobs/uid-1/files/zip")

    assert response.status_code == 502
    assert "The service is not reachable." in page(response).find("main").text


# --- the report ----------------------------------------------------------------------------------------------


def test_the_report_is_inline_in_a_sandbox(client, api):
    api.answers["get_file"] = file_answer("main.html", "text/html; charset=utf-8", b"<h1>R</h1>")

    response = client.get("/jobs/uid-1/report")

    assert ("get_file", "uid-1", "html") in api.calls
    assert response.data == b"<h1>R</h1>"
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"
    assert not response.headers["Content-Disposition"].startswith("attachment")
    assert response.headers["Content-Security-Policy"] == "sandbox allow-scripts"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_a_report_the_api_does_not_have_is_the_not_found_page(client, api):
    api.answers["get_file"] = problem(404, "JobNotFound")

    response = client.get("/jobs/uid-1/report")

    assert response.status_code == 404
    soup = page(response)
    assert NOT_FOUND in soup.find("main").text
    assert "Content-Security-Policy" not in response.headers


def test_ids_and_names_are_quoted_in_the_api_path(client, api):
    api.answers["get_file"] = file_answer("x", "text/plain")

    client.get(f"/jobs/uid-1/files/svg/{quote('a b.svg')}")

    assert ("get_file", "uid-1", "svg", "a b.svg") in api.calls
