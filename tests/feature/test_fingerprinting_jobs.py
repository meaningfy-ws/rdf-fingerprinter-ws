"""Binds the untagged scenarios of fingerprinting_jobs.feature (the others run in containers)."""

import uuid
from datetime import UTC, datetime
from pathlib import Path

from pytest_bdd import given, parsers, scenario, then, when

from fingerprinter.config import INPUT_MIME_TYPES
from fingerprinter.domain.model import FingerprintOutcome, JobRecord, JobState, ReportFormat, Source

FEATURE = "fingerprinting_jobs.feature"
ENDPOINT = "http://example.org/sparql"


@scenario(FEATURE, "A valid endpoint is queued")
def test_a_valid_endpoint_is_queued():
    pass


@scenario(FEATURE, "An invalid URL is rejected")
def test_an_invalid_url_is_rejected():
    pass


@scenario(FEATURE, "An RDF/XML file is queued")
def test_an_rdf_xml_file_is_queued():
    pass


@scenario(FEATURE, "An unsupported file is rejected")
def test_an_unsupported_file_is_rejected():
    pass


@scenario(FEATURE, "The dataset is removed after success")
def test_the_dataset_is_removed_after_success():
    pass


@scenario(FEATURE, "The dataset is removed after failure")
def test_the_dataset_is_removed_after_failure():
    pass


@scenario(FEATURE, "A just-accepted job is queued")
def test_a_just_accepted_job_is_queued():
    pass


@scenario(FEATURE, "An unknown job is not found")
def test_an_unknown_job_is_not_found():
    pass


@scenario(FEATURE, "Failed measurements are listed")
def test_failed_measurements_are_listed():
    pass


@scenario(FEATURE, "A running job can be cancelled")
def test_a_running_job_can_be_cancelled():
    pass


@scenario(FEATURE, "A finished job cannot be cancelled")
def test_a_finished_job_cannot_be_cancelled():
    pass


# --- submitting --------------------------------------------------------------------------------


@when(parsers.parse('a client posts the endpoint URL "{url}" with no graphs'))
def post_endpoint(world, url):
    world.submit_endpoint(url)


@when(parsers.parse('a client uploads the file "{filename}"'))
def upload_file(world, filename):
    world.upload(filename)


@then("the service answers 202 with a job id")
def answers_202(world):
    assert world.status == 202
    assert world.job_id


@then(parsers.parse('the job\'s state is "{state}"'))
def job_state_is(world, state):
    assert world.store.get(world.job_id).state == state


@then("no job is queued")
def no_job_is_queued(world):
    assert world.queue.submitted == []
    assert world.store.list() == []


@then("the service answers 415 with a problem response listing the accepted types")
def answers_415_with_types(world):
    assert world.status == 415
    assert set(world.problem["accepted"]) == set(INPUT_MIME_TYPES)


# --- file jobs ---------------------------------------------------------------------------------


@given(parsers.parse('a file job for "{filename}"'))
def a_file_job(world, filename):
    world.upload(filename)


@given("the library raises an error while fingerprinting")
def library_raises(world):
    world.library.error = RuntimeError("the library failed")


@when("the job completes")
def job_completes(world):
    world.run_file(world.job_id)
    assert world.store.get(world.job_id).state is JobState.COMPLETED


@when("the job fails")
def job_fails(world):
    world.run_file(world.job_id)
    assert world.store.get(world.job_id).state is JobState.FAILED


@then("its temporary dataset is deleted")
def dataset_deleted(world):
    name = f"fp-{world.job_id}"
    assert ("delete", name) in world.datasets.actions
    assert name not in world.datasets.datasets


@then("its upload folder is removed")
def upload_removed(world):
    assert world.job_id not in world.uploads.saved


# --- state -------------------------------------------------------------------------------------


@given("an endpoint job was accepted and no worker has taken it")
def accepted_endpoint_job(world):
    world.submit_endpoint(ENDPOINT)


@when("a client asks for its state")
def ask_state(world):
    world.status_of(world.job_id)


@then(parsers.parse('the service answers 200 with state "{state}"'))
def answers_200_with_state(world, state):
    assert world.status == 200
    assert world.result["state"] == state


@when(parsers.parse('a client asks for the state of job "{job_id}"'))
def ask_state_of(world, job_id):
    world.status_of(job_id)


@given("an endpoint on which two measurements fail but the report is written")
def two_measurements_fail(world):
    world.library.outcome = FingerprintOutcome(
        files={ReportFormat.HTML: (Path("main.html"),)},
        failures=("measurement one failed", "measurement two failed"),
    )
    world.submit_endpoint(ENDPOINT)


@when("the job ends")
def job_ends(world):
    world.run_endpoint(world.job_id, ENDPOINT)


@then(parsers.parse('its state is "{state}"'))
def its_state_is(world, state):
    assert world.store.get(world.job_id).state == state


@then("both failures are listed in the job state")
def failures_listed(world):
    assert world.store.get(world.job_id).failures == (
        "measurement one failed",
        "measurement two failed",
    )


# --- cancelling --------------------------------------------------------------------------------


@given("a file job that is queued")
def a_queued_file_job(world):
    world.upload("treaties-source-ap.rdf")


@given(parsers.parse('a job in state "{state}"'))
def a_job_in_state(world, state):
    world.job_id = str(uuid.uuid4())
    world.store.create(
        JobRecord(world.job_id, Source(endpoint=ENDPOINT), datetime.now(UTC), JobState(state))
    )


@when("a client cancels it")
def client_cancels(world):
    world.cancel(world.job_id)


@then(parsers.parse('its state becomes "{state}"'))
def state_becomes(world, state):
    assert world.status == 200
    assert world.store.get(world.job_id).state == state


@then("its upload is discarded and no outputs are kept")
def upload_discarded_no_outputs(world):
    assert world.job_id not in world.uploads.saved
    assert world.job_id not in world.store.outputs
    assert world.queue.cancelled == [world.job_id]


@then("the service answers 409")
def answers_409(world):
    assert world.status == 409


@then(parsers.parse('the job stays "{state}"'))
def job_stays(world, state):
    assert world.store.get(world.job_id).state == state
