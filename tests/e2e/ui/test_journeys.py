"""Journeys in a browser: a user starts a job and watches it finish, and deletes a report (job-console)."""

from collections.abc import Callable

from playwright.sync_api import Page, expect

JOB_WAIT_MS = 180_000


def row_for(page: Page, source: str):
    return page.locator("tr", has_text=source)


def test_start_an_endpoint_job_and_watch_it_finish(
    ui_url: str, continents_endpoint: str, open_page: Callable[..., Page]
):
    page = open_page()
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
    expect(page.locator("#announce")).to_contain_text("Done")


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
