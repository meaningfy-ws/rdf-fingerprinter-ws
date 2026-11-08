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
