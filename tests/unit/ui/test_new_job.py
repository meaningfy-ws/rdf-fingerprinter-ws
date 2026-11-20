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
        client.post(
            "/jobs/endpoint",
            data={"sparql_endpoint_url": "not a url", "graphs": "g1", "graphs_url": "not a url"},
        )
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
        client.post("/jobs/new/graphs", data={"sparql_endpoint_url": "http://e/sparql"}),
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
OTHER = "http://other/sparql"
G1, G2, G3 = "http://ex.org/g1", "http://ex.org/g2", "http://ex.org/g3"
OTHER_ENDPOINT = "These graphs belong to another endpoint. Load graphs again."


def choices(soup):
    return [(box["value"], box.has_attr("checked")) for box in soup.select("input[name=graphs]")]


def load(client, url=URL, **data):
    """What the "Load graphs" button sends: the endpoint form as the page holds it."""
    return client.post("/jobs/new/graphs", data={"sparql_endpoint_url": url, **data})


def submitted(form):
    """The data a browser posts for ``form``: its fields, and only the ticked checkboxes."""
    data: dict[str, list[str]] = {}
    for field in form.find_all("input"):
        if field.get("type") == "checkbox" and not field.has_attr("checked"):
            continue
        data.setdefault(field["name"], []).append(field.get("value", ""))
    return data


def test_before_graphs_are_loaded_the_form_offers_to_load_them(client):
    soup = page(client.get("/jobs/new"))

    group = soup.find("fieldset", id="graphs-picker")
    assert group.find("legend").text == "Named graphs (optional)"
    assert "Leave all unticked to profile every graph, including the default graph." in group.text
    assert "Select “Load graphs” to choose from the endpoint’s graphs." in group.text
    assert choices(soup) == []
    assert group["aria-describedby"] == "graphs-hint graphs-error"
    assert group.find(id="graphs-hint") and group.find(id="graphs-error")
    button = soup.find("button", string="Load graphs")
    assert (button["type"], button["hx-post"]) == ("button", "/jobs/new/graphs")
    assert (button["hx-include"], button["hx-target"]) == ("closest form", "#graphs-picker")
    assert not button.has_attr("hx-get")


def test_without_javascript_loading_graphs_is_a_second_submit_after_the_one_that_starts(client):
    form = page(client.get("/jobs/new")).find("form")

    names = [button.get("name") for button in form.find_all("button", type="submit")]
    start = form.find("button", string="Start fingerprinting")
    assert start.get("name") is None  # Enter in the URL field starts the job
    assert names == [None, "load_graphs"]


def test_two_graphs_are_chosen(client, api):
    api.answers["endpoint_graphs"] = (G1, G2, G3)

    fragment = page(load(client))

    assert ("endpoint_graphs", URL) in api.calls
    assert choices(fragment) == [(G1, False), (G2, False), (G3, False)]
    first = fragment.find("input", value=G1)
    assert fragment.find("label", attrs={"for": first["id"]}).find("code").text == G1
    assert fragment.find("input", attrs={"name": "graphs_url"})["value"] == URL
    assert fragment.find(id="announce").text == "3 named graphs found."

    client.post(
        "/jobs/endpoint",
        data={"sparql_endpoint_url": URL, "graphs": [G1, G3], "graphs_url": URL},
    )

    assert ("start_endpoint_job", URL, [G1, G3]) in api.calls


@pytest.mark.parametrize(
    ("listed", "sentence"),
    [((), "No named graphs found."), ((G1,), "1 named graph found.")],
)
def test_the_announcement_agrees_with_the_number_of_graphs(client, api, listed, sentence):
    api.answers["endpoint_graphs"] = listed

    assert page(load(client)).find(id="announce").text == sentence


def test_the_url_field_is_replaced_whole_and_follows_the_answer(client, api):
    api.answers["endpoint_graphs"] = problem(400, "InvalidSource")

    fragment = page(load(client, "not a url"))

    field = fragment.find(id="sparql_endpoint_url-field")
    assert field["hx-swap-oob"] == "outerHTML"
    assert field.find("input")["value"] == "not a url"
    assert field.find("input")["aria-invalid"] == "true"
    assert error_next_to(fragment, "sparql_endpoint_url") == URL_REFUSED
    assert choices(fragment) == []


def test_a_good_url_clears_an_earlier_url_error(client, api):
    fragment = page(load(client))

    field = fragment.find(id="sparql_endpoint_url-field")
    assert not field.find("input").has_attr("aria-invalid")
    assert error_next_to(fragment, "sparql_endpoint_url") == ""


def test_an_empty_url_for_the_graphs_is_refused_without_asking_the_api(client, api):
    fragment = page(load(client, ""))

    assert error_next_to(fragment, "sparql_endpoint_url") == URL_REFUSED
    assert api.calls == []


def test_ticks_survive_reloading_the_list(client, api):
    api.answers["endpoint_graphs"] = (G1, G2)

    fragment = page(load(client, graphs=[G2], graphs_url=URL))

    assert choices(fragment) == [(G1, False), (G2, True)]


def test_graphs_are_listed_without_javascript_on_the_new_job_page(client, api):
    api.answers["endpoint_graphs"] = (G1, G2)

    response = client.post(
        "/jobs/endpoint",
        data={"sparql_endpoint_url": URL, "load_graphs": "1", "graphs": [G2], "graphs_url": URL},
    )

    soup = page(response)
    assert ("endpoint_graphs", URL) in api.calls
    assert not [call for call in api.calls if call[0] == "start_endpoint_job"]
    assert soup.find("h1").text == "New job"
    assert soup.find("input", id="sparql_endpoint_url")["value"] == URL
    assert choices(soup) == [(G1, False), (G2, True)]
    assert soup.find("form")["action"] == "/jobs/endpoint"


def test_without_javascript_a_refused_url_is_said_at_the_field_and_nothing_is_listed(client, api):
    soup = page(client.post("/jobs/endpoint", data={"sparql_endpoint_url": "", "load_graphs": "1"}))

    assert error_next_to(soup, "sparql_endpoint_url") == URL_REFUSED
    assert api.calls == []


def test_the_rendered_checkboxes_are_posted_with_the_endpoint_form(client, api):
    api.answers["endpoint_graphs"] = (G1, G2)
    listed = client.post(
        "/jobs/endpoint",
        data={"sparql_endpoint_url": URL, "load_graphs": "1", "graphs": [G2]},
    )

    client.post("/jobs/endpoint", data=submitted(page(listed).find("form")))

    assert ("start_endpoint_job", URL, [G2]) in api.calls


def test_a_cross_site_get_lists_nothing(client, api):
    assert client.get("/jobs/new/graphs", query_string={"url": URL}).status_code == 405
    client.get("/jobs/new", query_string={"url": URL, "sparql_endpoint_url": URL})

    assert api.calls == []


def test_a_failed_submission_keeps_the_chosen_graphs_ticked(client, api):
    api.answers["start_endpoint_job"] = problem(503, "QueueUnavailable")

    soup = page(
        client.post(
            "/jobs/endpoint",
            data={"sparql_endpoint_url": URL, "graphs": [G1], "graphs_url": URL},
        )
    )

    assert choices(soup) == [(G1, True)]
    assert soup.find("input", attrs={"name": "graphs_url"})["value"] == URL


def test_graphs_loaded_for_another_endpoint_are_refused(client, api):
    soup = page(
        client.post(
            "/jobs/endpoint",
            data={"sparql_endpoint_url": OTHER, "graphs": [G1], "graphs_url": URL},
        )
    )

    assert OTHER_ENDPOINT in soup.find("fieldset", id="graphs-picker").text
    assert choices(soup) == [(G1, True)]
    assert soup.find("input", id="sparql_endpoint_url")["value"] == OTHER
    assert api.calls == []


def test_an_endpoint_without_named_graphs_says_so(client, api):
    api.answers["endpoint_graphs"] = ()

    fragment = page(load(client))

    assert choices(fragment) == []
    assert "This endpoint has no named graphs." in fragment.find("fieldset").text


def test_a_graph_iri_with_markup_is_escaped(client, api):
    iri = "http://ex.org/<script>alert(1)</script>"
    api.answers["endpoint_graphs"] = (iri,)

    response = load(client)

    assert b"<script>alert(1)</script>" not in response.data
    assert page(response).find("code").text == iri


# --- The endpoint cannot be reached for its graphs -----------------------------------------------------


def test_the_endpoint_cannot_be_reached_for_its_graphs(client, api):
    detail = "the endpoint could not be reached"
    api.answers["endpoint_graphs"] = problem(502, "GraphListingFailed", detail=detail)

    fragment = page(load(client))

    group = fragment.find("fieldset", id="graphs-picker")
    assert "Could not list the graphs: the endpoint could not be reached." in group.text
    assert group.find(id="graphs-error").find(class_="field-error")
    assert choices(fragment) == []
    assert "Could not list the graphs" in fragment.find(id="announce").text

    client.post("/jobs/endpoint", data={"sparql_endpoint_url": URL})  # still submits, no graphs

    assert ("start_endpoint_job", URL, []) in api.calls


def test_a_failed_reload_keeps_the_ticked_graphs_under_the_sentence(client, api):
    api.answers["endpoint_graphs"] = problem(502, "GraphListingFailed", detail="it is down")

    fragment = page(load(client, OTHER, graphs=[G1], graphs_url=URL))

    group = fragment.find("fieldset", id="graphs-picker")
    assert "Could not list the graphs: it is down." in group.text
    assert choices(fragment) == [(G1, True)]
    assert fragment.find("input", attrs={"name": "graphs_url"})["value"] == URL  # still URL's


def test_an_api_that_gives_no_answer_for_the_graphs_is_said(client, api):
    api.answers["endpoint_graphs"] = unreachable()

    fragment = page(load(client))

    assert "The service is not reachable." in fragment.find("fieldset").text


def test_an_endpoint_that_does_not_answer_in_time_is_not_a_service_outage(client, api):
    detail = "the endpoint did not answer in time"
    api.answers["endpoint_graphs"] = problem(504, "GraphListingFailed", detail=detail)

    text = page(load(client)).find("fieldset").text

    assert "Could not list the graphs: the endpoint did not answer in time." in text
    assert "not reachable" not in text
