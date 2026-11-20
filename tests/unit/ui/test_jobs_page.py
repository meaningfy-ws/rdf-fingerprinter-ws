"""The Jobs page and its rows fragment: the job-console scenarios on listing and live status."""

import json
import time
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

import pytest

from fingerprinter.entrypoints.ui.exceptions import ApiError
from tests.unit.ui.fake_api import page, problem, record, unreachable

NOW = datetime(2026, 11, 8, 14, 30, tzinfo=UTC)


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    with monkeypatch.context() as patched:
        patched.setenv("TZ", "UTC")
        time.tzset()
        patched.setattr("fingerprinter.entrypoints.ui.views.utcnow", lambda: NOW)
        yield
    time.tzset()  # the zone of the environment again, now that TZ is restored


def rows_of(soup):
    return soup.find("tbody", id="job-rows").find_all("tr")


def names(row):
    """The visible words of each cell of a row."""
    return [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]


# --- Jobs in every state are listed ---------------------------------------------------------------


def test_jobs_in_every_state_are_listed(client, api):
    api.jobs = [
        record("done", "completed", created_at="2026-11-08T09:00:00+00:00"),
        record("bad", "failed", reason="endpoint unreachable: http://e/sparql",
               created_at="2026-11-08T10:00:00+00:00"),
        record("busy", "running", created_at="2026-11-08T14:25:00+00:00"),
    ]  # fmt: skip

    soup = page(client.get("/"))

    rows = rows_of(soup)
    assert [row["id"] for row in rows] == ["job-busy", "job-bad", "job-done"]  # newest first
    assert [row.find(class_="badge").get_text(strip=True) for row in rows] == [
        "Running…",
        "Failed",
        "Done",
    ]
    assert all("http://e/sparql" in row.get_text() for row in rows)


def test_a_row_names_the_source_the_kind_the_time_and_the_note(client, api):
    api.jobs = [
        record("a", "completed", source={"endpoint": "http://e/sparql", "graphs": ["g1", "g2"]},
               created_at="2026-11-08T14:21:00+00:00"),
        record("b", "completed", source={"file": "treaties.rdf", "graphs": []},
               created_at="2026-11-07T08:05:00+00:00"),
        record("c", "completed_with_failures", failures=["m1", "m2"],
               created_at="2026-11-01T08:05:00+00:00"),
        record("d", "failed", reason="x" * 100, created_at="2026-10-01T08:05:00+00:00"),
    ]  # fmt: skip

    a, b, c, d = rows_of(page(client.get("/")))

    assert names(a)[:3] == ["http://e/sparql SPARQL endpoint · 2 named graphs", "9 min ago",
                            "Done Took 2.4 s"]  # fmt: skip
    assert names(b)[:3] == ["treaties.rdf RDF file", "Yesterday, 08:05", "Done Took 2.4 s"]
    assert "2 parts could not be produced" in names(c)[2]
    assert "Done with warnings" in names(c)[2]
    assert names(d)[2] == "Failed " + "x" * 79 + "…"
    time_tag = a.find("time")
    assert time_tag["datetime"] == "2026-11-08T14:21:00+00:00"
    assert time_tag["title"] == "8 Nov 2026, 14:21"
    assert c.find("time").get_text() == "1 Nov 2026, 08:05"


def test_a_row_names_its_job_in_the_menu_for_screen_readers(client, api):
    api.jobs = [record("a", "failed", source={"file": "treaties.rdf", "graphs": []})]

    summary = rows_of(page(client.get("/")))[0].find("summary")

    assert summary.get_text(strip=True) == "Actions for treaties.rdf"


# --- outputs and the menu follow the state (U-3) -------------------------------------------------


def next_of(link) -> str:
    return parse_qs(urlsplit(link["href"]).query)["next"][0]


def row_links(row):
    return {a.get_text(" ", strip=True): a for a in row.find_all("a")}


@pytest.mark.parametrize("state", ["completed", "completed_with_failures"])
def test_a_finished_job_offers_its_report_its_zip_and_delete(client, api, state):
    api.jobs = [record("j1", state, failures=["m"] if state != "completed" else [])]

    links = row_links(rows_of(page(client.get("/")))[0])

    assert links["Open report"]["href"] == "/jobs/j1"  # the Job page, from stage 2
    assert not links["Open report"].has_attr("target")
    assert links["Download all (.zip)"]["href"] == "/jobs/j1/files/zip"
    assert urlsplit(links["Delete…"]["href"]).path == "/jobs/j1/delete"
    assert next_of(links["Delete…"]) == "/"
    assert "Cancel job…" not in links


@pytest.mark.parametrize("state", ["queued", "running"])
def test_an_active_job_offers_cancel_and_no_output(client, api, state):
    api.jobs = [record("j1", state)]

    links = row_links(rows_of(page(client.get("/?show=active")))[0])

    assert list(links) == ["Cancel job…"]
    assert urlsplit(links["Cancel job…"]["href"]).path == "/jobs/j1/cancel"
    assert next_of(links["Cancel job…"]) == "/?show=active"


@pytest.mark.parametrize("state", ["failed", "cancelled"])
def test_a_stopped_job_offers_only_delete(client, api, state):
    api.jobs = [record("j1", state)]

    assert list(row_links(rows_of(page(client.get("/")))[0])) == ["Delete…"]


# --- the four filters -----------------------------------------------------------------------------

EVERY_STATE = ["queued", "running", "completed", "completed_with_failures", "failed", "cancelled"]


@pytest.mark.parametrize(
    ("show", "shown"),
    [
        ("all", EVERY_STATE),
        ("active", ["queued", "running"]),
        ("finished", ["completed", "completed_with_failures"]),
        ("stopped", ["failed", "cancelled"]),
        ("nonsense", EVERY_STATE),
    ],
)
def test_each_filter_lists_its_states(client, api, show, shown):
    api.jobs = [record(state, state) for state in EVERY_STATE]

    ids = [row["id"] for row in rows_of(page(client.get(f"/?show={show}")))]

    assert sorted(ids) == sorted(f"job-{state}" for state in shown)


def test_the_filters_are_links_and_the_current_one_is_marked(client, api):
    api.jobs = [record()]

    nav = page(client.get("/?show=finished")).find("nav", attrs={"aria-label": "Filter jobs"})

    links = {a.get_text(strip=True): a for a in nav.find_all("a")}
    assert list(links) == ["All", "In progress", "Finished", "Failed or cancelled"]
    assert links["All"]["href"] == "/"
    assert links["Failed or cancelled"]["href"] == "/?show=stopped"
    assert [name for name, a in links.items() if a.get("aria-current") == "page"] == ["Finished"]


def test_a_filter_without_jobs_says_so_and_offers_all(client, api):
    api.jobs = [record("j1", "completed")]

    soup = page(client.get("/?show=active"))

    body = soup.find("tbody", id="job-rows")
    assert "No jobs here." in body.get_text()
    assert body.find("a", string="Show all")["href"] == "/"


# --- An empty console says so ----------------------------------------------------------------------


def test_an_empty_console_says_so(client, api):
    soup = page(client.get("/"))

    main = soup.find("main")
    assert "No jobs yet." in main.get_text()
    links = {a.get_text(strip=True): a["href"] for a in main.find_all("a")}
    assert links["SPARQL endpoint"] == "/jobs/new?from=endpoint"
    assert links["RDF file"] == "/jobs/new?from=file"
    assert links["New job"] == "/jobs/new"
    assert soup.find("table") is None


# --- A running job reaches completion / Finished jobs do not poll ----------------------------------


def poll_attributes(tbody):
    return {key: tbody.get(key) for key in ("hx-get", "hx-trigger", "hx-swap", "hx-vals")}


def test_a_page_with_an_active_job_polls_with_the_ids_active_now(client, api):
    api.jobs = [record("r", "running"), record("q", "queued"), record("d", "completed")]

    attributes = poll_attributes(page(client.get("/")).find("tbody", id="job-rows"))

    assert attributes["hx-trigger"] == "every 3s"
    assert attributes["hx-swap"] == "outerHTML"
    assert attributes["hx-get"] == "/jobs/rows?show=all"
    assert sorted(json.loads(attributes["hx-vals"])["was"].split(",")) == ["q", "r"]


def test_a_running_job_reaches_completion(client, api):
    api.jobs = [record("j1", "running", source={"file": "treaties-source-ap.rdf", "graphs": []})]
    first = page(client.get("/jobs/rows?show=all&was="))
    assert first.find("tbody")["hx-trigger"] == "every 3s"
    assert first.find(id="announce").get_text() == ""  # nothing ended yet

    api.jobs = [record("j1", "completed", source={"file": "treaties-source-ap.rdf", "graphs": []})]
    done = page(client.get("/jobs/rows?show=all&was=j1"))

    assert done.find(class_="badge").get_text(strip=True) == "Done"
    assert done.find("a", href="/jobs/j1") is not None
    assert poll_attributes(done.find("tbody")) == dict.fromkeys(poll_attributes(done), None)
    announce = done.find(id="announce")
    assert announce["hx-swap-oob"] == "innerHTML"
    assert announce.get_text() == "treaties-source-ap.rdf: Done."
    assert page(client.get("/jobs/rows?show=all&was=")).find(id="announce").get_text() == ""


def test_the_poll_after_a_change_names_only_the_jobs_still_active(client, api):
    api.jobs = [record("a", "running"), record("b", "completed")]

    body = page(client.get("/jobs/rows?show=all&was=a,b")).find("tbody", id="job-rows")

    assert json.loads(body["hx-vals"]) == {"was": "a"}


def test_every_job_that_ended_is_announced_once_with_its_label(client, api):
    api.jobs = [
        record("a", "failed", source={"file": "a.rdf", "graphs": []}),
        record("b", "cancelled", source={"file": "b.rdf", "graphs": []}),
        record("c", "running"),
        record("gone-from-the-list", "completed", source={"file": "z.rdf", "graphs": []}),
    ]

    soup = page(client.get("/jobs/rows?show=all&was=a,b,c,deleted"))

    assert soup.find(id="announce").get_text() == "a.rdf: Failed. b.rdf: Cancelled."


def test_a_job_that_ends_under_the_in_progress_filter_is_announced_and_polling_stops(client, api):
    api.jobs = [record("j1", "completed", source={"file": "t.rdf", "graphs": []})]

    soup = page(client.get("/jobs/rows?show=active&was=j1"))

    assert soup.find(id="announce").get_text() == "t.rdf: Done."
    assert "No jobs here." in soup.find("tbody").get_text()
    assert soup.find("tbody").get("hx-trigger") is None


def test_finished_jobs_do_not_poll(client, api):
    api.jobs = [record("d", "completed"), record("f", "failed"), record("x", "cancelled")]

    for url in ("/", "/jobs/rows?show=all&was="):
        soup = page(client.get(url))
        assert not [tag for tag in soup.find_all(True) if "hx-trigger" in tag.attrs], url
        assert not [tag for tag in soup.find_all(True) if "hx-get" in tag.attrs], url


def test_an_active_job_that_the_filter_hides_is_not_polled(client, api):
    api.jobs = [record("r", "running"), record("d", "completed")]

    assert page(client.get("/?show=finished")).find("tbody").get("hx-trigger") is None


# --- the service is down --------------------------------------------------------------------------


def test_a_page_says_when_the_service_is_not_reachable(client, api):
    api.answers["list_jobs"] = unreachable()

    response = client.get("/")

    assert response.status_code == 200
    alert = page(response).find(class_="flash-error")
    assert alert.get_text(strip=True) == "The service is not reachable. Try again in a moment."
    assert page(response).find("table") is None


def test_a_poll_while_the_service_is_down_pauses_and_keeps_polling(client, api):
    api.answers["list_jobs"] = unreachable()

    response = client.get("/jobs/rows?show=active&was=a,b")

    assert response.status_code == 200
    body = page(response).find("tbody", id="job-rows")
    assert [row.get_text(strip=True) for row in body.find_all("tr")] == [
        "Status updates paused: the service is not reachable."
    ]
    assert body["hx-trigger"] == "every 3s"
    assert body["hx-get"] == "/jobs/rows?show=active"
    assert json.loads(body["hx-vals"]) == {"was": "a,b"}


def test_an_error_answer_from_the_api_is_shown_as_its_sentence(client, api):
    api.answers["list_jobs"] = problem(503, "QueueUnavailable")

    soup = page(client.get("/"))

    assert "The job queue is unavailable. Try again later." in soup.find(class_="flash-error").text


def test_an_answer_that_is_not_json_is_a_server_error(client, api):
    api.answers["list_jobs"] = ApiError(None, 502)

    soup = page(client.get("/"))

    assert "Something went wrong on the server. Try again." in soup.find(class_="flash-error").text


def test_a_poll_answered_with_an_error_says_so_in_the_row_and_keeps_polling(client, api):
    api.answers["list_jobs"] = problem(500)

    response = client.get("/jobs/rows?show=active&was=a")

    body = page(response).find("tbody", id="job-rows")
    assert [row.get_text(strip=True) for row in body.find_all("tr")] == [
        "Something went wrong on the server. Try again."
    ]
    assert body["hx-trigger"] == "every 3s"
    assert json.loads(body["hx-vals"]) == {"was": "a"}


# --- one odd record cannot break the page ----------------------------------------------------------


def test_a_state_the_ui_does_not_know_is_shown_as_it_came_with_a_neutral_badge(client, api):
    api.jobs = [record("odd", "paused-by-ops"), record("ok", "completed")]

    response = client.get("/")

    assert response.status_code == 200
    odd, ok = (page(response).find("tr", id=f"job-{name}") for name in ("odd", "ok"))
    badge = odd.find(class_="badge")
    assert badge.get_text(strip=True) == "paused-by-ops"
    assert "badge-unknown" in badge["class"]
    assert not [a for a in odd.find_all("a") if "/report" in a["href"]]  # no outputs, not active
    assert ok.find(class_="badge").get_text(strip=True) == "Done"
    assert page(client.get("/?show=active")).find("tr", id="job-odd") is None


def test_a_record_without_graphs_is_a_row_like_any_other(client, api):
    odd = record("odd", "completed")
    odd["source"] = {"endpoint": "http://e/sparql"}
    del odd["failures"]
    api.jobs = [odd]

    row = page(client.get("/")).find("tr", id="job-odd")

    assert "SPARQL endpoint · all graphs" in row.get_text(" ", strip=True)
    assert row.find(class_="badge").get_text(strip=True) == "Done"


def test_the_page_says_it_updates_by_itself(client, api):
    api.jobs = [record()]

    assert "Updates by itself while a job is queued or running." in page(client.get("/")).text


def test_the_rows_url_carries_the_filter(client, api):
    api.jobs = [record("r", "running")]

    body = page(client.get("/jobs/rows?show=active&was=r")).find("tbody")

    query = parse_qs(urlsplit(body["hx-get"]).query)
    assert query == {"show": ["active"]}
