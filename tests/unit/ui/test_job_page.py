"""The Job page: the report-viewer scenarios on reading a job's report, diagram and downloads."""

import time
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

import pytest

from tests.unit.ui.fake_api import page, problem, record, served, unreachable

NOW = datetime(2026, 11, 8, 14, 30, tzinfo=UTC)
SOURCE = "http://e/sparql"
FILES = {
    "html": ["main.html"],
    "json": ["profile.json"],
    "shacl": ["shapes-default.ttl"],
    "puml": ["diagram-default.puml", "diagram-default--skos.puml"],
    "svg": ["diagram-default--skos.svg", "diagram-default.svg"],
    "pattern": ["pattern.txt"],
    "shex": ["shapes.shex"],
    "pitfalls": ["pitfalls.tsv"],
}
DIAGRAM_HEADERS = "default-src 'none'; style-src 'unsafe-inline'; sandbox; frame-ancestors 'self'"


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    with monkeypatch.context() as patched:
        patched.setenv("TZ", "UTC")
        time.tzset()
        patched.setattr("fingerprinter.entrypoints.ui.views.utcnow", lambda: NOW)
        yield
    time.tzset()


def done(state="completed", **fields):
    fields = {"files": FILES, "created_at": "2026-11-08T14:21:00+00:00"} | fields
    return record("j1234567-aaaa", state, **fields)


def open_job(client, api, query="", **fields):
    api.jobs = [done(**fields)]
    return page(client.get(f"/jobs/j1234567-aaaa{query}"))


def tabs_of(soup):
    return {
        a.get_text(strip=True): a
        for a in soup.find("nav", attrs={"aria-label": "Job"}).find_all("a")
    }


# --- The report is read in the page ------------------------------------------------------------------


def test_the_report_is_read_in_the_page(client, api):
    soup = open_job(client, api)

    frame = soup.find("iframe")
    assert frame["sandbox"] == ["allow-scripts"]  # scripts, but no same-origin access
    assert frame["src"] == "/jobs/j1234567-aaaa/report"
    assert SOURCE in frame["title"]
    new_tab = soup.find("a", string="Open in a new tab")
    assert (new_tab["href"], new_tab["target"], new_tab["rel"]) == (
        "/jobs/j1234567-aaaa/report", "_blank", ["noopener"],
    )  # fmt: skip


@pytest.mark.parametrize("query", ["", "?tab=report", "?tab=nope", "?tab="])
def test_a_missing_or_unknown_tab_opens_the_report(client, api, query):
    soup = open_job(client, api, query)

    assert soup.find("iframe") is not None
    assert tabs_of(soup)["Report"]["aria-current"] == "page"


def test_the_tabs_are_links_to_the_page_states(client, api):
    tabs = tabs_of(open_job(client, api))

    assert list(tabs) == ["Report", "Class diagram", "Downloads"]
    assert [parse_qs(urlsplit(a["href"]).query)["tab"] for a in tabs.values()] == [
        ["report"], ["diagram"], ["downloads"],
    ]  # fmt: skip
    assert all(urlsplit(a["href"]).path == "/jobs/j1234567-aaaa" for a in tabs.values())


# --- The diagram is shown ---------------------------------------------------------------------------


def test_the_diagram_is_shown(client, api):
    soup = open_job(client, api, "?tab=diagram")

    image = soup.find("img")
    assert image["src"] == "/jobs/j1234567-aaaa/diagrams/diagram-default.svg"  # the whole model
    assert SOURCE in image["alt"]
    assert tabs_of(soup)["Class diagram"]["aria-current"] == "page"
    download = soup.find("a", href="/jobs/j1234567-aaaa/files/svg/diagram-default.svg")
    assert download.get_text(strip=True) == "Download SVG"
    assert soup.find("iframe") is None


def test_the_picker_lists_the_whole_model_then_each_vocabulary(client, api):
    soup = open_job(client, api, "?tab=diagram")

    form = soup.find("form", attrs={"method": "get"})
    assert form["action"] == "/jobs/j1234567-aaaa"
    assert form.find("input", attrs={"name": "tab"})["value"] == "diagram"
    select = form.find("select", attrs={"name": "diagram"})
    assert [(o["value"], o.get_text(strip=True)) for o in select.find_all("option")] == [
        ("diagram-default.svg", "Whole model"),
        ("diagram-default--skos.svg", "Vocabulary: skos"),
    ]
    assert form.find("button").get_text(strip=True) == "Show"
    assert form["hx-trigger"] == "change"  # htmx submits on change; the button serves without it


def test_another_diagram_is_chosen_by_its_file(client, api):
    soup = open_job(client, api, "?tab=diagram&diagram=diagram-default--skos.svg")

    assert soup.find("img")["src"].endswith("/diagrams/diagram-default--skos.svg")
    assert soup.find("option", selected=True)["value"] == "diagram-default--skos.svg"
    assert soup.find("a", href="/jobs/j1234567-aaaa/files/svg/diagram-default--skos.svg")


def test_an_unknown_diagram_shows_the_first_and_says_so(client, api):
    soup = open_job(client, api, "?tab=diagram&diagram=nothing.svg")

    assert soup.find("img")["src"].endswith("/diagrams/diagram-default.svg")
    assert soup.find(class_="flash").get_text(strip=True) == "That diagram does not exist."


def test_with_several_graphs_each_diagram_names_its_graph(client, api):
    files = FILES | {"svg": ["diagram-a.svg", "diagram-b.svg", "diagram-a--foaf.svg"]}
    api.jobs = [done(files=files)]
    soup = page(client.get("/jobs/j1234567-aaaa?tab=diagram"))

    labels = [o.get_text(strip=True) for o in soup.find_all("option")]
    assert labels == ["Whole model — a", "Whole model — b", "Vocabulary: foaf — a"]


def test_a_vocabulary_split_in_parts_names_each_part(client, api):
    parts = ["diagram-default--skos~1.svg", "diagram-default--skos~2.svg"]
    api.jobs = [
        done(files=FILES | {"svg": ["diagram-default.svg", "diagram-default--dct.svg", *parts]})
    ]
    soup = page(client.get("/jobs/j1234567-aaaa?tab=diagram"))

    labels = [o.get_text(strip=True) for o in soup.find_all("option")]
    assert labels == [
        "Whole model", "Vocabulary: dct", "Vocabulary: skos (part 1)", "Vocabulary: skos (part 2)",
    ]  # fmt: skip


# --- The diagram failed to render -------------------------------------------------------------------


def test_the_diagram_failed_to_render(client, api):
    failures = [
        "Class diagram diagram-default could not be drawn: the PlantUML server is not reachable"
    ]
    files = {name: names for name, names in FILES.items() if name != "svg"}
    soup = open_job(client, api, "?tab=diagram", state="completed_with_failures", files=files,
                    failures=failures)  # fmt: skip

    assert soup.find("img") is None
    panel = soup.find(id="diagram")
    assert "No diagram is available." in panel.text
    assert failures[0] in panel.text


# --- Downloads are listed ---------------------------------------------------------------------------


def test_downloads_are_listed(client, api):
    soup = open_job(client, api, "?tab=downloads")

    rows = soup.find("table").find("tbody").find_all("tr")
    shown = [[c.get_text(" ", strip=True) for c in row.find_all(["th", "td"])] for row in rows]
    assert [row[1] for row in shown] == [
        "main.html",
        "profile.json",
        "shapes-default.ttl",
        "2 files (.zip)",
        "2 files (.zip)",
        "pattern.txt",
        "shapes.shex",
        "pitfalls.tsv",
        "10 files (.zip)",
    ]
    names = [row.find("th").find(class_="name").get_text(strip=True) for row in rows]
    assert names == [
        "Report", "Profile (JSON)", "SHACL shapes", "Class diagram (PlantUML)",
        "Class diagram (SVG)", "Pattern schema", "ShEx schema", "Pitfalls (TSV)",
        "Download all (.zip)",
    ]  # fmt: skip
    assert "The report page, to keep or share." in rows[0].text
    links = [row.find("a")["href"] for row in rows]
    assert links[0] == "/jobs/j1234567-aaaa/files/html"
    assert links[-1] == "/jobs/j1234567-aaaa/files/zip"
    assert all(row.find("a").get_text(" ", strip=True).startswith("Download") for row in rows)


def test_a_format_the_job_does_not_hold_has_no_row(client, api):
    files = {name: names for name, names in FILES.items() if name not in ("svg", "pitfalls")}
    soup = open_job(client, api, "?tab=downloads", files=files)

    text = soup.find("table").text
    assert "Class diagram (SVG)" not in text
    assert "Pitfalls (TSV)" not in text
    assert "Download all (.zip)" in text


# --- The header, the warnings and the actions -------------------------------------------------------


def test_the_header_names_the_source_the_state_the_time_the_duration_and_the_short_id(client, api):
    soup = open_job(client, api)

    assert soup.find("h1").get_text(strip=True) == SOURCE
    assert soup.find(class_="badge").get_text(strip=True) == "Done"
    meta = soup.find(class_="meta")
    assert meta.find("time")["title"] == "8 Nov 2026, 14:21"
    for part in ("SPARQL endpoint · all graphs", "9 min ago", "Took 2.4 s", "j1234567"):
        assert part in meta.get_text(" ", strip=True)
    assert "j1234567-aaaa" not in meta.text  # the short id, not the whole one
    assert soup.title.get_text().startswith(SOURCE)


def test_a_finished_job_offers_delete_that_comes_back_to_the_page(client, api):
    soup = open_job(client, api)

    delete = soup.find("a", string="Delete…")
    assert urlsplit(delete["href"]).path == "/jobs/j1234567-aaaa/delete"
    assert parse_qs(urlsplit(delete["href"]).query)["next"] == ["/jobs/j1234567-aaaa"]
    assert soup.find("a", string="Cancel job…") is None


def test_the_warnings_panel_lists_the_failures_and_counts_them(client, api):
    soup = open_job(client, api, state="completed_with_failures", failures=["first", "second"])

    panel = soup.find("details", class_="warnings")
    assert panel.find("summary").get_text(strip=True) == "Some parts could not be produced (2)"
    assert [li.get_text(strip=True) for li in panel.find_all("li")] == ["first", "second"]
    assert soup.find("iframe") is not None  # the report is still there


def test_a_job_without_failures_has_no_warnings_panel(client, api):
    assert open_job(client, api).find("details") is None


# --- An unreachable endpoint ------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["failed", "cancelled"])
def test_a_job_that_stopped_offers_no_report_diagram_or_download(client, api, state):
    reason = "endpoint unreachable: http://e/sparql" if state == "failed" else None
    api.jobs = [record("j1", state, reason=reason)]

    soup = page(client.get("/jobs/j1?tab=downloads"))

    assert soup.find("nav", attrs={"aria-label": "Job"}) is None
    assert soup.find(["iframe", "img", "table"]) is None
    assert soup.find("a", string="Delete…") is not None
    assert soup.find(class_="badge").get_text(strip=True) == state.capitalize()


def test_a_job_without_outputs_has_no_diagram_to_complain_about(client, api):
    api.jobs = [record("j1", "failed", reason="endpoint unreachable")]

    soup = page(client.get("/jobs/j1?tab=diagram&diagram=nothing.svg"))

    assert soup.find(class_="flash") is None


def test_an_unreachable_endpoint(client, api):
    reason = "endpoint unreachable: http://e/sparql: connection refused"
    api.jobs = [record("j1", "failed", reason=reason)]

    soup = page(client.get("/jobs/j1"))

    assert soup.find(class_="badge").get_text(strip=True) == "Failed"
    assert reason in soup.find("main").text  # the whole reason, not the row's summary
    assert soup.find("iframe") is None


# --- A job in progress ------------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["queued", "running"])
def test_an_active_job_shows_a_status_block_that_polls_and_offers_cancel(client, api, state):
    api.jobs = [record("j1", state)]

    soup = page(client.get("/jobs/j1"))

    block = soup.find(id="job-status")
    assert block["hx-get"] == "/jobs/j1/state"
    assert block["hx-trigger"] == "every 3s"
    assert (
        block.find(class_="badge").get_text(strip=True)
        == {"queued": "Queued", "running": "Running…"}[state]
    )
    assert soup.find("nav", attrs={"aria-label": "Job"}) is None
    cancel = soup.find("a", string="Cancel job…")
    assert parse_qs(urlsplit(cancel["href"]).query)["next"] == ["/jobs/j1"]
    assert soup.find("a", string="Delete…") is None


def test_a_final_job_does_not_poll(client, api):
    soup = open_job(client, api)

    assert not [
        tag
        for tag in soup.find_all(True)
        if tag.has_attr("hx-trigger") and "every" in tag["hx-trigger"]
    ]


def test_the_state_fragment_keeps_polling_while_the_job_is_active(client, api):
    api.jobs = [record("j1", "running")]

    response = client.get("/jobs/j1/state")

    assert "HX-Refresh" not in response.headers
    assert page(response).find(id="job-status")["hx-trigger"] == "every 3s"


@pytest.mark.parametrize("state", ["completed", "completed_with_failures", "failed", "cancelled"])
def test_the_state_fragment_asks_for_a_refresh_once_the_job_is_final(client, api, state):
    api.jobs = [record("j1", state)]

    assert client.get("/jobs/j1/state").headers["HX-Refresh"] == "true"


def test_the_state_fragment_of_a_job_that_is_gone_reloads_to_the_not_found_page(client, api):
    api.jobs = []

    response = client.get("/jobs/gone/state")

    assert response.status_code == 200
    assert response.headers["HX-Refresh"] == "true"


@pytest.mark.parametrize(
    ("answer", "sentence"),
    [
        (unreachable(), "Status updates paused: the service is not reachable."),
        (problem(500), "Something went wrong on the server. Try again."),
    ],
)
def test_a_poll_the_api_cannot_answer_says_so_and_polls_again(client, api, answer, sentence):
    api.answers["job"] = answer

    response = client.get("/jobs/j1/state")

    assert response.status_code == 200
    block = page(response).find(id="job-status")
    assert sentence in block.text
    assert block["hx-trigger"] == "every 3s"


# --- Jobs that are not there, and the API being down -------------------------------------------------


def test_an_unknown_job_is_the_not_found_page(client, api):
    response = client.get("/jobs/nope")

    assert response.status_code == 404
    assert "No such job or report." in page(response).find("main").text


def test_the_job_page_while_the_service_is_down_says_so(client, api):
    api.answers["job"] = unreachable()

    response = client.get("/jobs/j1")

    assert response.status_code == 502
    assert "The service is not reachable." in page(response).find("main").text


# --- The diagram route ------------------------------------------------------------------------------


def test_a_diagram_is_inline_and_cannot_run_anything(client, api):
    api.answers["file"] = served("diagram-default.svg", "image/svg+xml", b"<svg/>")

    response = client.get("/jobs/j1/diagrams/diagram-default.svg")

    assert ("file", "j1", "svg", "diagram-default.svg") in api.calls
    assert response.data == b"<svg/>"
    assert response.headers["Content-Type"].startswith("image/svg+xml")
    assert response.headers["Content-Disposition"].startswith("inline")
    assert response.headers["Content-Security-Policy"] == DIAGRAM_HEADERS
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_a_diagram_the_api_does_not_list_is_the_not_found_page(client, api):
    api.answers["file"] = problem(404, "FormatNotAvailable")

    response = client.get("/jobs/j1/diagrams/other.svg")

    assert response.status_code == 404
    assert "No such job or report." in page(response).find("main").text
