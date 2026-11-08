"""Journeys in a browser: a user starts a job and watches it finish, and deletes a report (job-console)."""

import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

JOB_WAIT_MS = 180_000
POLL_INTERVAL_MS = 3_000
SETTLE_MS = 500


def row_for(page: Page, source: str):
    return page.locator("tr", has_text=source)


def test_start_an_endpoint_job_and_watch_it_finish(
    ui_url: str, continents_endpoint: str, quiet_console: None, open_page: Callable[..., Page]
):
    page = open_page()
    polls: list[str] = []
    page.on(
        "request",
        lambda request: polls.append(request.url) if "/jobs/rows" in request.url else None,
    )
    page.goto(f"{ui_url}/jobs/new")

    page.get_by_label("SPARQL endpoint URL").fill(continents_endpoint)
    page.get_by_role("button", name="Start fingerprinting").click()

    expect(page.get_by_role("status")).to_have_text("Job started.")
    row = row_for(page, continents_endpoint)
    expect(row).to_be_visible()
    page.evaluate("window.sameDocument = true")  # a reload would lose this
    expect(row).to_contain_text("Done", timeout=JOB_WAIT_MS)
    assert page.evaluate("window.sameDocument") is True
    expect(row.get_by_role("link", name="Open report")).to_be_visible()
    ended = rf"^{re.escape(continents_endpoint)}: Done( with warnings)?\.$"
    expect(page.locator("#announce")).to_have_text(re.compile(ended))  # said once, not repeated
    page.wait_for_timeout(SETTLE_MS)  # the browser's last request events reach this test
    polls_when_done = len(polls)
    page.wait_for_timeout(POLL_INTERVAL_MS + 1_500)  # longer than one polling interval
    assert len(polls) == polls_when_done, "the page kept polling after the job was done"


def test_delete_with_confirmation(
    ui_url: str, finished_job: str, finished_source: str, open_page: Callable[..., Page]
):
    source = finished_source
    page = open_page()
    page.goto(ui_url)

    def choose_delete():
        row_for(page, source).locator("summary").click()
        page.get_by_role("link", name="Delete…").click()
        expect(page.get_by_role("alertdialog")).to_contain_text(source)

    choose_delete()
    page.get_by_role("link", name="Keep it").click()
    expect(row_for(page, source)).to_be_visible()

    choose_delete()
    page.get_by_role("button", name="Delete report").click()
    expect(page.get_by_role("status")).to_contain_text("deleted")
    expect(row_for(page, source)).to_have_count(0)


def test_open_a_jobs_report_diagram_and_a_download(
    ui_url: str, continents_job: str, open_page: Callable[..., Page]
):
    page = open_page()
    page.goto(f"{ui_url}/jobs/{continents_job}")

    report = page.frame_locator("iframe[title^='Report for']")
    expect(report.locator("body")).to_have_text(re.compile(r"\S"))  # the library's page, loaded

    page.get_by_role("link", name="Class diagram").click()
    image = page.get_by_role("img", name=re.compile("Class diagram of"))
    expect(image).to_be_visible()
    page.wait_for_function("document.querySelector('#diagram img').naturalWidth > 0")
    options = page.get_by_label("Diagram").locator("option")
    assert options.count() > 1  # the whole model and a vocabulary
    before = image.get_attribute("src")
    page.get_by_label("Diagram").select_option(index=1)  # chosen without leaving the page
    expect(image).not_to_have_attribute("src", before)
    page.wait_for_function("document.querySelector('#diagram img').naturalWidth > 0")

    page.get_by_role("link", name="Downloads").click()
    with page.expect_download() as download:
        page.get_by_role("link", name="Download Profile (JSON)").click()
    assert download.value.suggested_filename.endswith(".json")
