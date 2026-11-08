"""Accessibility in a browser: no external assets, both themes, a 360 px screen, the keyboard (report-viewer)."""

from collections.abc import Callable
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.ui.conftest import UNREACHABLE, axe_violations

PHONE = {"width": 360, "height": 740}
PAGES = (
    "jobs",
    "new job from an endpoint",
    "new job from a file",
    "delete confirmation",
    "job report",
    "job class diagram",
    "job downloads",
    "failed job",
)


@pytest.fixture(scope="module")
def paths(continents_job: str, finished_job: str):
    """The paths to check; the Jobs page lists a finished job of each kind (Done, Failed)."""
    return {
        "jobs": "/",
        "new job from an endpoint": "/jobs/new",
        "new job from a file": "/jobs/new?from=file",
        "delete confirmation": f"/jobs/{finished_job}/delete",
        "job report": f"/jobs/{continents_job}",
        "job class diagram": f"/jobs/{continents_job}?tab=diagram",
        "job downloads": f"/jobs/{continents_job}?tab=downloads",
        "failed job": f"/jobs/{finished_job}",
    }


@pytest.mark.parametrize("name", PAGES)
def test_no_external_assets(name, ui_url, paths, open_page: Callable[..., Page]):
    page = open_page()
    requested = []
    page.on("request", lambda request: requested.append(request.url))

    page.goto(ui_url + paths[name])
    page.wait_for_load_state("networkidle")

    foreign = [url for url in requested if urlsplit(url).netloc != urlsplit(ui_url).netloc]
    assert requested and not foreign


@pytest.mark.parametrize("color_scheme", ["light", "dark"])
@pytest.mark.parametrize("name", PAGES)
def test_both_themes_pass(name, color_scheme, ui_url, paths, open_page: Callable[..., Page]):
    page = open_page(color_scheme)
    page.goto(ui_url + paths[name])

    assert axe_violations(page) == []


@pytest.mark.parametrize("name", PAGES)
def test_a_phone_screen_needs_no_sideways_scroll(
    name, ui_url, paths, open_page: Callable[..., Page]
):
    page = open_page(viewport=PHONE)
    page.goto(ui_url + paths[name])

    widths = page.evaluate(
        "[document.documentElement.scrollWidth, document.documentElement.clientWidth]"
    )
    assert widths[0] <= widths[1], widths
    assert axe_violations(page) == []


def test_the_keyboard_alone_starts_a_job(ui_url, open_page: Callable[..., Page]):
    endpoint = UNREACHABLE.format("keyboard")
    page = open_page()
    page.goto(ui_url)

    def focused_text() -> str:
        return page.evaluate("document.activeElement.textContent || ''")

    def tab_until(is_there: Callable[[], bool]) -> None:
        for _ in range(30):
            page.keyboard.press("Tab")
            if is_there():
                return
        pytest.fail("the keyboard never reached it")

    tab_until(lambda: "New job" in focused_text())
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="New job")).to_be_visible()
    tab_until(lambda: page.evaluate("document.activeElement.id") == "sparql_endpoint_url")
    page.keyboard.type(endpoint)
    page.keyboard.press("Enter")

    expect(page.get_by_role("status")).to_have_text("Job started.")
    in_new_row = f"!!document.activeElement.closest('tr')?.textContent.includes('{endpoint}')"
    tab_until(lambda: page.evaluate(in_new_row))
