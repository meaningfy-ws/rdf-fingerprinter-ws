"""The New job page: the job-console scenarios on starting a job."""

from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from fingerprinter.entrypoints.ui import create_app
from fingerprinter.entrypoints.ui.exceptions import ApiError
from tests.unit.ui.fake_api import make_app, page, problem, record, unreachable

URL_REFUSED = "Enter an http or https SPARQL endpoint URL, without a user name or password."


def post_file(client, name="data.ttl", content=b"data", **options):
    data = {"data_file": FileStorage(BytesIO(content), name)}
    return client.post("/jobs/file", data=data, content_type="multipart/form-data", **options)


def error_next_to(soup, field_id):
    return soup.find(id=f"{field_id}-error").get_text(" ", strip=True)


# --- the page ---------------------------------------------------------------------------------------


def test_the_endpoint_tab_is_the_default_and_names_its_fields(client):
    soup = page(client.get("/jobs/new"))

    tabs = {
        a.get_text(strip=True): a
        for a in soup.find("nav", attrs={"aria-label": "Where the data comes from"}).find_all("a")
    }
    assert list(tabs) == ["From an endpoint", "From a file"]
    assert tabs["From an endpoint"]["aria-current"] == "page"
    assert tabs["From a file"]["href"] == "/jobs/new?from=file"
    url = soup.find("input", id="sparql_endpoint_url")
    assert soup.find("label", attrs={"for": "sparql_endpoint_url"}).text == "SPARQL endpoint URL"
    assert url["name"] == "sparql_endpoint_url"
    assert soup.find("form")["action"] == "/jobs/endpoint"
    assert soup.find("textarea") is None
    assert soup.find("button", string="Start fingerprinting")["type"] == "submit"
    assert soup.find("a", string="Cancel")["href"] == "/"


def test_the_file_tab_lists_the_accepted_types_and_the_limit(client):
    soup = page(client.get("/jobs/new?from=file"))

    tabs = {
        a.get_text(strip=True): a
        for a in soup.find("nav", attrs={"aria-label": "Where the data comes from"}).find_all("a")
    }
    assert tabs["From a file"]["aria-current"] == "page"
    form = soup.find("form")
    assert (form["action"], form["enctype"]) == ("/jobs/file", "multipart/form-data")
    upload = form.find("input", type="file")
    assert upload["accept"] == ".rdf,.ttl"
    assert soup.find(id="data_file-hint").text == "Accepted: .rdf, .ttl. Up to 2 MB."
    assert soup.find("label", attrs={"for": "data_file"}).text == "RDF file"


@pytest.mark.parametrize("path", ["/jobs/new", "/jobs/new?from=file"])
def test_what_you_get_explains_each_output(client, path):
    panel = page(client.get(path)).find("aside")

    assert panel.find("h2").text == "What you get"
    terms = [dt.text for dt in panel.find_all("dt")]
    assert terms[:3] == ["Report", "Profile (JSON)", "SHACL shapes"]
    assert terms[-1] == "Download all (.zip)"
    assert "Every measurement, for tools and scripts." in panel.text
    assert "Class diagram (SVG)" in terms


def test_the_header_new_job_button_opens_the_new_job_page(client):
    button = page(client.get("/")).find("header").find("a", class_="btn-primary")

    assert (button.get_text(strip=True), button["href"]) == ("New job", "/jobs/new")


def test_the_forms_carry_a_csrf_token(api):
    client = make_app(api, csrf=True).test_client()

    for path in ("/jobs/new", "/jobs/new?from=file"):
        assert page(client.get(path)).find("input", attrs={"name": "csrf_token"})["value"]


# --- An endpoint job is started ----------------------------------------------------------------------


def test_an_endpoint_job_is_started(client, api):
    api.jobs = [
        record("j1", "queued", source={"endpoint": "http://example.org/sparql", "graphs": []})
    ]
    response = client.post(
        "/jobs/endpoint",
        data={"sparql_endpoint_url": "http://example.org/sparql"},
        follow_redirects=True,
    )

    assert ("start_endpoint_job", "http://example.org/sparql", []) in api.calls
    soup = page(response)
    assert soup.find(class_="flash-success").text.strip() == "Job started."
    assert soup.find("h1").text == "Jobs"
    row = soup.find("tr", id="job-j1")
    assert "http://example.org/sparql" in row.get_text()
    assert row.find(class_="badge").get_text(strip=True) == "Queued"


# --- An invalid URL is refused -----------------------------------------------------------------------


def test_an_invalid_url_is_refused(client, api):
    api.answers["start_endpoint_job"] = problem(400, "InvalidSource")

    soup = page(
        client.post("/jobs/endpoint", data={"sparql_endpoint_url": "not a url", "graphs": "g1"})
    )

    assert soup.find("input", id="sparql_endpoint_url")["value"] == "not a url"
    assert soup.find("input", attrs={"name": "graphs"})["value"] == "g1"
    assert error_next_to(soup, "sparql_endpoint_url") == URL_REFUSED
    assert soup.find("input", id="sparql_endpoint_url")["aria-invalid"] == "true"
    assert soup.find(class_="flash") is None


def test_an_empty_url_is_refused_without_asking_the_api(client, api):
    soup = page(client.post("/jobs/endpoint", data={"sparql_endpoint_url": ""}))

    assert error_next_to(soup, "sparql_endpoint_url") == URL_REFUSED
    assert api.calls == []


@pytest.mark.parametrize(
    ("answer", "sentence"),
    [
        (problem(503, "QueueUnavailable"), "The job queue is unavailable. Try again later."),
        (problem(500), "Something went wrong on the server. Try again."),
        (unreachable(), "The service is not reachable. Try again in a moment."),
    ],
)
def test_other_refusals_of_an_endpoint_job_are_said_next_to_the_url(client, api, answer, sentence):
    api.answers["start_endpoint_job"] = answer

    soup = page(client.post("/jobs/endpoint", data={"sparql_endpoint_url": "http://e/sparql"}))

    assert error_next_to(soup, "sparql_endpoint_url") == sentence
    assert soup.find("input", id="sparql_endpoint_url")["value"] == "http://e/sparql"


# --- An unsupported file is refused --------------------------------------------------------------------


def test_a_file_job_is_started(client, api):
    response = post_file(client, follow_redirects=True)

    assert ("start_file_job", "data.ttl") in api.calls
    assert page(response).find(class_="flash-success").text.strip() == "Job started."


def test_an_unsupported_file_is_refused(client, api):
    api.answers["start_file_job"] = problem(415, "UnsupportedFileType", accepted=["rdf", "ttl"])

    soup = page(post_file(client, "notes.docx"))

    assert (
        error_next_to(soup, "data_file") == "This file type is not supported. Accepted: rdf, ttl."
    )
    assert soup.find("a", attrs={"aria-current": "page"}).text == "From a file"


def test_a_missing_file_is_refused_without_asking_the_api(client, api):
    soup = page(client.post("/jobs/file", data={}, content_type="multipart/form-data"))

    assert error_next_to(soup, "data_file") == "Choose a file to upload."
    assert api.calls == []


def test_the_api_refusing_a_large_file_names_the_limit(client, api):
    api.answers["start_file_job"] = problem(413, "UploadTooLarge")

    soup = page(post_file(client))

    assert error_next_to(soup, "data_file") == "The file is too large (limit 2 MB)."


def test_a_request_beyond_the_limit_plus_a_megabyte_never_reaches_the_api(api):
    app = create_app("http://api.test", "k", accepted_extensions=("ttl",), max_upload_bytes=1024)
    app.config["WTF_CSRF_ENABLED"] = False
    app.extensions["api"] = api
    assert app.config["MAX_CONTENT_LENGTH"] == 1024 + 1024 * 1024

    response = app.test_client().post(
        "/jobs/file",
        data={"data_file": FileStorage(BytesIO(b"x" * (1024 * 1024 + 2048)), "big.ttl")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 413
    assert error_next_to(page(response), "data_file") == "The file is too large (limit 1 MB)."
    assert api.calls == []


def test_a_post_without_the_csrf_token_is_refused(api):
    client = make_app(api, csrf=True).test_client()

    for response in (
        client.post("/jobs/endpoint", data={"sparql_endpoint_url": "http://e/sparql"}),
        post_file(client),
    ):
        assert response.status_code == 400
    assert api.calls == []


def test_a_response_with_no_json_is_still_a_sentence(client, api):
    api.answers["start_endpoint_job"] = ApiError(None, 502)

    soup = page(client.post("/jobs/endpoint", data={"sparql_endpoint_url": "http://e/sparql"}))

    assert (
        error_next_to(soup, "sparql_endpoint_url")
        == "Something went wrong on the server. Try again."
    )


# --- Two graphs are chosen -----------------------------------------------------------------------------

URL = "http://e/sparql"
G1, G2, G3 = "http://ex.org/g1", "http://ex.org/g2", "http://ex.org/g3"


def choices(soup):
    return [(box["value"], box.has_attr("checked")) for box in soup.select("input[name=graphs]")]


def test_before_graphs_are_loaded_the_form_offers_to_load_them(client):
    soup = page(client.get("/jobs/new"))

    group = soup.find("fieldset", id="graphs-picker")
    assert group.find("legend").text == "Named graphs (optional)"
    assert "Leave all unticked to profile every graph, including the default graph." in group.text
    assert "Select “Load graphs” to choose from the endpoint’s graphs." in group.text
    assert choices(soup) == []
    button = soup.find("button", string="Load graphs")
    assert (button["type"], button["hx-get"]) == ("button", "/jobs/new/graphs")
    assert button["hx-target"] == "#graphs-picker"
    without_script = soup.find("noscript").find("button")  # Enter must not load graphs
    assert without_script["formaction"] == "/jobs/new" and without_script["formmethod"] == "get"


def test_two_graphs_are_chosen(client, api):
    api.answers["endpoint_graphs"] = (G1, G2, G3)

    fragment = page(client.get("/jobs/new/graphs", query_string={"url": URL}))

    assert ("endpoint_graphs", URL) in api.calls
    assert choices(fragment) == [(G1, False), (G2, False), (G3, False)]
    first = fragment.find("input", value=G1)
    assert fragment.find("label", attrs={"for": first["id"]}).find("code").text == G1
    assert fragment.find(id="announce").text == "3 named graphs found."

    client.post("/jobs/endpoint", data={"sparql_endpoint_url": URL, "graphs": [G1, G3]})

    assert ("start_endpoint_job", URL, [G1, G3]) in api.calls


def test_graphs_are_listed_without_javascript_on_the_new_job_page(client, api):
    api.answers["endpoint_graphs"] = (G1, G2)

    soup = page(client.get("/jobs/new", query_string={"url": URL, "graphs": G2}))

    assert soup.find("input", id="sparql_endpoint_url")["value"] == URL
    assert choices(soup) == [(G1, False), (G2, True)]
    assert soup.find("form")["action"] == "/jobs/endpoint"


def test_a_failed_submission_keeps_the_chosen_graphs_ticked(client, api):
    api.answers["start_endpoint_job"] = problem(503, "QueueUnavailable")

    soup = page(client.post("/jobs/endpoint", data={"sparql_endpoint_url": URL, "graphs": [G1]}))

    assert choices(soup) == [(G1, True)]


def test_an_endpoint_without_named_graphs_says_so(client, api):
    api.answers["endpoint_graphs"] = ()

    fragment = page(client.get("/jobs/new/graphs", query_string={"url": URL}))

    assert choices(fragment) == []
    assert "This endpoint has no named graphs." in fragment.find("fieldset").text


# --- The endpoint cannot be reached for its graphs -----------------------------------------------------


def test_the_endpoint_cannot_be_reached_for_its_graphs(client, api):
    detail = "the endpoint could not be reached"
    api.answers["endpoint_graphs"] = problem(502, "GraphListingFailed", detail=detail)

    fragment = page(client.get("/jobs/new/graphs", query_string={"url": URL}))

    group = fragment.find("fieldset", id="graphs-picker")
    assert "Could not list the graphs: the endpoint could not be reached." in group.text
    assert choices(fragment) == []
    assert "Could not list the graphs" in fragment.find(id="announce").text

    client.post("/jobs/endpoint", data={"sparql_endpoint_url": URL})  # still submits, no graphs

    assert ("start_endpoint_job", URL, []) in api.calls


def test_an_api_that_gives_no_answer_for_the_graphs_is_said(client, api):
    api.answers["endpoint_graphs"] = unreachable()

    fragment = page(client.get("/jobs/new/graphs", query_string={"url": URL}))

    assert "The service is not reachable." in fragment.find("fieldset").text


def test_an_invalid_url_for_the_graphs_is_said_next_to_the_url(client, api):
    api.answers["endpoint_graphs"] = problem(400, "InvalidSource")

    fragment = page(client.get("/jobs/new/graphs", query_string={"url": "not a url"}))

    error = fragment.find(id="sparql_endpoint_url-error")
    assert error["hx-swap-oob"] == "innerHTML" and error.text.strip() == URL_REFUSED
    assert choices(fragment) == []
    full = page(client.get("/jobs/new", query_string={"url": "not a url"}))
    assert error_next_to(full, "sparql_endpoint_url") == URL_REFUSED


def test_a_good_url_clears_an_earlier_url_error(client, api):
    fragment = page(client.get("/jobs/new/graphs", query_string={"url": URL}))

    assert fragment.find(id="sparql_endpoint_url-error").text.strip() == ""


def test_an_empty_url_for_the_graphs_is_refused_without_asking_the_api(client, api):
    fragment = page(client.get("/jobs/new/graphs"))

    assert fragment.find(id="sparql_endpoint_url-error").text.strip() == URL_REFUSED
    assert api.calls == []
