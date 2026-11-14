"""Binds the untagged scenarios of job_console.feature (the @unit ones are proven elsewhere)."""

import re

import pytest
from bs4 import BeautifulSoup
from pytest_bdd import given, parsers, scenario, then, when

import fingerprinter.entrypoints.ui as ui
from tests.unit.ui.fake_api import FakeApi, make_app, record

FEATURE = "job_console.feature"
MEANINGFY = "https://meaningfy.lu"
REPOSITORY = "https://github.com/meaningfy-ws/rdf-fingerprinter-ws"
LICENCE = f"{REPOSITORY}/blob/main/LICENSE"
SENTINEL_VERSION = "9.9.9-test"
CREDIT = "Made with love by Meaningfy"
MISSING_JOB = "/jobs/nope"
PAGES = {
    "the jobs list": "/",
    "the new-job page": "/jobs/new",
    "the job's report viewer": "/jobs/j1",
    "the page of a job that does not exist": MISSING_JOB,
}


@scenario(FEATURE, "Every page ends with the footer")
def test_every_page_ends_with_the_footer():
    pass


@scenario(FEATURE, "The footer shows the installed version")
def test_the_footer_shows_the_installed_version(sentinel_version):
    pass


@scenario(FEATURE, "The heart is hidden from assistive technology")
def test_the_heart_is_hidden_from_assistive_technology():
    pass


@pytest.fixture
def sentinel_version(monkeypatch):
    """The footer's only source is the UI's `version`: answer a value no template can know."""
    monkeypatch.setattr(ui, "version", lambda _package: SENTINEL_VERSION)


@pytest.fixture
def api() -> FakeApi:
    return FakeApi()


@pytest.fixture
def console():
    return {}


def _footer(console) -> BeautifulSoup:
    return console["page"].find("footer")


@given("the API holds a completed job")
def api_holds_a_job(api):
    api.jobs = [record("j1", "completed")]


@when(parsers.parse("a user opens {page}"))
def user_opens(api, console, page):
    response = make_app(api).test_client().get(PAGES[page])
    console["page"] = BeautifulSoup(response.data, "html.parser")
    console["status"] = response.status_code
    console["path"] = PAGES[page]


@then(parsers.parse('the page ends with a footer that reads "{text}"'))
def page_ends_with_footer(console, text):
    assert console["status"] == (404 if console["path"] == MISSING_JOB else 200)
    body = console["page"].find("body")
    assert [tag.name for tag in body.find_all(recursive=False)][-1] == "footer"
    assert re.sub(r"\s+", " ", _footer(console).get_text(" ")).strip().startswith(text)


@then(
    parsers.parse(
        "the footer links to the Meaningfy website, the repository and the licence, "
        'each with rel "{rel}"'
    )
)
def footer_links(console, rel):
    links = _footer(console).find_all("a")
    assert [a["href"] for a in links] == [MEANINGFY, REPOSITORY, LICENCE]
    for link in links:
        assert rel in link["rel"]


@then(parsers.parse('the footer shows "{prefix}" followed by the version of the installed package'))
def footer_shows_version(console, prefix):
    text = re.sub(r"\s+", " ", _footer(console).get_text(" "))
    assert f"{prefix}{SENTINEL_VERSION}" in text


@then("the heart and the logo drawing are marked aria-hidden")
def heart_and_logo_hidden(console):
    footer = _footer(console)
    assert footer.find(class_="heart")["aria-hidden"] == "true"
    logo = footer.find("svg", class_="logo-meaningfy")
    assert logo["aria-hidden"] == "true"


@then(parsers.parse('the footer\'s text still reads "{text}"'))
def footer_text(console, text):
    assert re.sub(r"\s+", " ", _footer(console).get_text(" ")).strip().startswith(text)
