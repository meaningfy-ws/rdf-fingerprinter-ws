"""Binds the untagged scenarios of report_access.feature (the @unit ones are proven elsewhere)."""

import uuid

from pytest_bdd import given, parsers, scenario, then, when

from fingerprinter.domain.model import FingerprintOutcome, JobState, ReportFormat
from tests.fakes import JobFailed

FEATURE = "report_access.feature"
ENDPOINT = "http://example.org/sparql"


@scenario(FEATURE, "A completed job appears in the list")
def test_a_completed_job_appears_in_the_list():
    pass


@scenario(FEATURE, "A failed job appears without formats")
def test_a_failed_job_appears_without_formats():
    pass


@scenario(FEATURE, "The report page is downloaded")
def test_the_report_page_is_downloaded():
    pass


@scenario(FEATURE, "An unknown format is rejected")
def test_an_unknown_format_is_rejected():
    pass


@scenario(FEATURE, "An unknown report is not found")
def test_an_unknown_report_is_not_found():
    pass


@scenario(FEATURE, "A format with no file is not found")
def test_a_format_with_no_file_is_not_found():
    pass


@scenario(FEATURE, "A report is deleted")
def test_a_report_is_deleted():
    pass


@scenario(FEATURE, "All reports are deleted")
def test_all_reports_are_deleted():
    pass


@scenario(FEATURE, "Deleting an unknown report")
def test_deleting_an_unknown_report():
    pass


def complete_a_job(world, url=ENDPOINT):
    job_id = world.submit_endpoint(url)
    world.run_endpoint(job_id, url)
    return job_id


# --- givens ------------------------------------------------------------------------------------


@given(parsers.parse('a job that completed for "{url}"'))
def a_job_completed_for(world, url):
    complete_a_job(world, url)


@given(parsers.parse('a job that failed because "{url}" was unreachable'))
def a_job_failed(world, url):
    world.library.error = JobFailed(f"endpoint unreachable: {url}")
    complete_a_job(world, url)


@given("a completed report")
def a_completed_report(world):
    world.job_id = complete_a_job(world)


@given("two completed reports")
def two_completed_reports(world):
    complete_a_job(world)
    complete_a_job(world)


@given(parsers.parse('a completed report whose "{format_name}" output holds no file'))
def a_report_with_an_empty_output(world, format_name):
    world.library.outcome = FingerprintOutcome(
        files={**world.library.outcome.files, ReportFormat(format_name): ()}
    )
    world.job_id = complete_a_job(world)


# --- whens -------------------------------------------------------------------------------------


@when("a client lists the reports")
def client_lists(world):
    world.list_reports()


@when(parsers.parse('a client downloads its format "{format_name}"'))
def client_downloads(world, format_name):
    world.download(world.job_id, format_name)


@when(
    parsers.parse(
        'a client downloads format "{format_name}" of a report id the service never issued'
    )
)
def client_downloads_unknown(world, format_name):
    world.download(str(uuid.uuid4()), format_name)


@when("a client deletes it")
def client_deletes(world):
    world.delete(world.job_id)


@when("a client deletes all reports")
def client_deletes_all(world):
    world.delete_all()


@when("a client deletes a report id the service never issued")
def client_deletes_unknown(world):
    world.delete(str(uuid.uuid4()))


# --- thens -------------------------------------------------------------------------------------


@then(
    parsers.parse(
        'the list holds that report with its source, state "completed" and its seven formats'
    )
)
def list_holds_completed(world):
    (record,) = world.result
    assert record["source"]["endpoint"] == ENDPOINT
    assert record["state"] == JobState.COMPLETED
    # the seven the library writes; the worker adds the class diagrams it drew (svg)
    assert [name for name in record["formats"] if name != "svg"] == [
        "html",
        "json",
        "shacl",
        "puml",
        "pattern",
        "shex",
        "pitfalls",
    ]


@then(parsers.parse('the list holds that job with state "failed", its reason, and no formats'))
def list_holds_failed(world):
    (record,) = world.result
    assert record["state"] == JobState.FAILED
    assert record["reason"] == "endpoint unreachable: http://unreachable.invalid/sparql"
    assert record["formats"] == []


@then(parsers.parse('it receives "{name}" as "{mime_type}"'))
def receives_file(world, name, mime_type):
    assert world.status == 200
    assert world.response.headers["content-type"].startswith(mime_type)
    assert f"filename={name}" in world.response.headers["content-disposition"]


@then("it is no longer listed and its files are gone")
def report_gone(world):
    assert world.status == 200
    assert world.store.list() == []
    assert world.store.outputs == {}


@then("the service answers 200 and the list is empty")
def all_gone(world):
    assert world.status == 200
    assert world.store.list() == []
