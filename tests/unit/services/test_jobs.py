import io
from datetime import UTC, datetime
from pathlib import Path

import pytest

from fingerprinter.domain.exceptions import (
    InvalidSource,
    JobNotCancellable,
    JobNotFound,
    QueueUnavailable,
    UnsupportedFileType,
)
from fingerprinter.domain.model import FingerprintOutcome, JobRecord, JobState, ReportFormat, Source
from fingerprinter.services import jobs
from tests.fakes import (
    FakeDatasetStore,
    FakeFingerprinter,
    FakeJobQueue,
    FakeUploadStore,
    InMemoryJobStore,
)

URL = "http://example.org/sparql"
EXTENSIONS = frozenset({"rdf", "ttl"})
FINISHED = datetime(2026, 11, 8, 10, 0, 7, tzinfo=UTC)


@pytest.fixture
def store():
    return InMemoryJobStore()


@pytest.fixture
def queue():
    return FakeJobQueue()


@pytest.fixture
def uploads():
    return FakeUploadStore()


@pytest.fixture
def datasets():
    return FakeDatasetStore()


@pytest.fixture
def library():
    return FakeFingerprinter()


def submit_file(store, uploads, queue, name="data.ttl"):
    return jobs.submit_file_job(
        io.BytesIO(b"x"), name, supported_extensions=EXTENSIONS, job_store=store, upload_store=uploads,
        queue=queue,
    )  # fmt: skip


def run_endpoint(store, library, job_id, graphs=()):
    jobs.run_endpoint_job(job_id, URL, graphs, job_store=store, fingerprinter=library)


def run_file(store, datasets, uploads, library, job_id):
    jobs.run_file_job(
        job_id, uploads.saved[job_id], job_store=store, dataset_store=datasets, upload_store=uploads,
        fingerprinter=library,
    )  # fmt: skip


# --- submit_endpoint_job -----------------------------------------------------------------------


def test_submitting_an_endpoint_records_a_queued_job_and_queues_it(store, queue):
    job_id = jobs.submit_endpoint_job(URL, ("http://g",), job_store=store, queue=queue)
    record = store.get(job_id)
    assert record.state is JobState.QUEUED
    assert record.source == Source(endpoint=URL, graphs=("http://g",))
    assert queue.submitted == [(job_id, URL)]


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.org/sparql",
        "example.org",
        "http://",
        "",
        "https://user:secret@example.org/sparql",
        "https://user@example.org/sparql",
        "https://:secret@example.org/sparql",
    ],
)
def test_an_endpoint_that_is_not_http_is_rejected_without_a_job(url, store, queue):
    with pytest.raises(InvalidSource):
        jobs.submit_endpoint_job(url, (), job_store=store, queue=queue)
    assert store.list() == []
    assert queue.submitted == []


def test_an_endpoint_with_a_query_string_is_kept_as_given(store, queue):
    url = "https://example.org/sparql?default-graph-uri=http%3A%2F%2Fg"
    job_id = jobs.submit_endpoint_job(url, (), job_store=store, queue=queue)
    assert store.get(job_id).source.endpoint == url


def test_a_failure_other_than_the_queue_being_unavailable_is_not_swallowed(store, queue):
    queue.error = ValueError("a bug")
    with pytest.raises(ValueError, match="a bug"):
        jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)


def test_an_unavailable_queue_fails_the_endpoint_job(store, queue):
    queue.error = QueueUnavailable("redis down")
    with pytest.raises(QueueUnavailable):
        jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    (record,) = store.list()
    assert record.state is JobState.FAILED
    assert record.reason == "queue unavailable"


# --- submit_file_job ---------------------------------------------------------------------------


def test_submitting_a_file_saves_the_upload_records_a_queued_job_and_queues_it(
    store, uploads, queue
):
    job_id = submit_file(store, uploads, queue)
    assert store.get(job_id).state is JobState.QUEUED
    assert store.get(job_id).source == Source(file="data.ttl")
    assert queue.submitted == [(job_id, str(uploads.saved[job_id]))]


def test_the_extension_check_ignores_case(store, uploads, queue):
    assert submit_file(store, uploads, queue, name="DATA.TTL")


def test_an_unsupported_file_is_rejected_without_upload_or_job(store, uploads, queue):
    with pytest.raises(UnsupportedFileType) as error:
        submit_file(store, uploads, queue, name="notes.txt")
    assert error.value.accepted == ("rdf", "ttl")
    assert (store.list(), uploads.saved, queue.submitted) == ([], {}, [])


def test_an_unavailable_queue_discards_the_upload_and_fails_the_file_job(store, uploads, queue):
    queue.error = QueueUnavailable("redis down")
    with pytest.raises(QueueUnavailable):
        submit_file(store, uploads, queue)
    (record,) = store.list()
    assert record.state is JobState.FAILED
    assert uploads.saved == {}


# --- run_endpoint_job --------------------------------------------------------------------------


def test_a_run_without_failures_completes_with_the_saved_formats(store, queue, library):
    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    run_endpoint(store, library, job_id)
    record = store.get(job_id)
    assert record.state is JobState.COMPLETED
    assert record.formats == library.outcome.formats
    assert library.calls == [(URL, ())]


def test_a_run_with_failures_completes_with_failures_listed(store, queue, library):
    library.outcome = FingerprintOutcome(
        files={ReportFormat.HTML: (Path("main.html"),)}, failures=("a failed", "b failed")
    )
    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    run_endpoint(store, library, job_id)
    record = store.get(job_id)
    assert record.state is JobState.COMPLETED_WITH_FAILURES
    assert record.failures == ("a failed", "b failed")
    assert record.formats == (ReportFormat.HTML,)


def test_a_library_error_fails_the_job_with_the_message_and_keeps_no_outputs(store, queue, library):
    library.error = RuntimeError("endpoint unreachable: x")
    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    run_endpoint(store, library, job_id)
    record = store.get(job_id)
    assert (record.state, record.reason) == (JobState.FAILED, "endpoint unreachable: x")
    assert job_id not in store.outputs


def test_the_work_folder_is_removed_after_the_run(store, queue):
    seen = []

    class Spy(FakeFingerprinter):
        def fingerprint(self, endpoint_url, graphs, work_folder):
            assert work_folder.is_dir()
            seen.append(work_folder)
            return super().fingerprint(endpoint_url, graphs, work_folder)

    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    run_endpoint(store, Spy(), job_id)
    assert not seen[0].exists()


def test_a_job_cancelled_before_the_task_starts_is_left_alone(store, queue, library):
    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    store.set_state(job_id, JobState.CANCELLED)
    run_endpoint(store, library, job_id)
    assert store.get(job_id).state is JobState.CANCELLED
    assert library.calls == []


def test_a_job_cancelled_while_running_keeps_its_state_and_no_outputs(store, queue):
    class CancelsMidRun(FakeFingerprinter):
        def fingerprint(self, endpoint_url, graphs, work_folder):
            store.set_state(job_id, JobState.CANCELLED)
            return super().fingerprint(endpoint_url, graphs, work_folder)

    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    run_endpoint(store, CancelsMidRun(), job_id)
    assert store.get(job_id).state is JobState.CANCELLED
    assert store.get(job_id).formats == ()
    assert job_id not in store.outputs


def test_a_job_cancelled_while_running_is_not_overwritten_by_a_failure(store, queue):
    class CancelsThenFails(FakeFingerprinter):
        def fingerprint(self, endpoint_url, graphs, work_folder):
            store.set_state(job_id, JobState.CANCELLED)
            raise RuntimeError("killed")

    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    run_endpoint(store, CancelsThenFails(), job_id)
    assert store.get(job_id).state is JobState.CANCELLED


class StoreFailingToSaveOutputs(InMemoryJobStore):
    """Writes part of the outputs, then fails, as a full disk would."""

    def save_outputs(self, job_id, outcome):
        super().save_outputs(job_id, outcome)
        raise OSError("disk full")


def test_a_failure_while_saving_outputs_discards_them_before_recording_failed(queue, library):
    store = StoreFailingToSaveOutputs()
    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    run_endpoint(store, library, job_id)
    record = store.get(job_id)
    assert (record.state, record.reason) == (JobState.FAILED, "disk full")
    assert record.formats == ()
    assert job_id not in store.outputs


@pytest.mark.parametrize("state", [JobState.RUNNING, JobState.COMPLETED, JobState.FAILED])
def test_a_job_that_is_not_queued_is_not_run_again(state, store, queue, library):
    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    run_endpoint(store, library, job_id)
    store.set_state(job_id, state)
    outputs = dict(store.outputs[job_id])
    library.calls.clear()
    run_endpoint(store, library, job_id)
    assert library.calls == []
    assert store.get(job_id).state is state
    assert store.outputs[job_id] == outputs


def test_a_duplicate_delivery_of_a_running_file_job_leaves_its_dataset_and_upload(
    store, queue, uploads, datasets, library
):
    job_id = submit_file(store, uploads, queue)
    store.set_state(job_id, JobState.RUNNING)
    datasets.datasets[jobs.dataset_name(job_id)] = None
    run_file(store, datasets, uploads, library, job_id)
    assert jobs.dataset_name(job_id) in datasets.datasets
    assert job_id in uploads.saved


# --- run_file_job ------------------------------------------------------------------------------


def test_a_file_job_fingerprints_its_temporary_dataset_then_removes_it_and_the_upload(
    store, queue, uploads, datasets, library
):
    job_id = submit_file(store, uploads, queue)
    run_file(store, datasets, uploads, library, job_id)
    name = jobs.dataset_name(job_id)
    assert store.get(job_id).state is JobState.COMPLETED
    assert [a for a in datasets.actions if a[1] == name] == [
        ("create", name), ("load_file", name), ("delete", name),
    ]  # fmt: skip
    assert library.calls == [(datasets.sparql_url(name), ())]
    assert uploads.saved == {}


def test_a_failing_file_job_still_removes_the_dataset_and_the_upload(
    store, queue, uploads, datasets, library
):
    library.error = RuntimeError("boom")
    job_id = submit_file(store, uploads, queue)
    run_file(store, datasets, uploads, library, job_id)
    assert store.get(job_id).state is JobState.FAILED
    assert ("delete", jobs.dataset_name(job_id)) in datasets.actions
    assert uploads.saved == {}


@pytest.mark.parametrize(
    ("error", "final_state"),
    [(None, JobState.COMPLETED), (RuntimeError("boom"), JobState.FAILED)],
)
def test_a_file_job_removes_its_dataset_and_upload_before_its_final_state_is_recorded(
    error, final_state, store, queue, uploads, library
):
    datasets = FakeDatasetStore(store)
    library.error = error
    job_id = submit_file(store, uploads, queue)
    run_file(store, datasets, uploads, library, job_id)
    assert datasets.state_at_delete == {jobs.dataset_name(job_id): JobState.RUNNING}
    assert store.get(job_id).state is final_state
    assert uploads.saved == {}


def test_a_dataset_that_cannot_be_created_fails_the_file_job(
    store, queue, uploads, datasets, library
):
    datasets.fail_on_create = RuntimeError("fuseki down")
    job_id = submit_file(store, uploads, queue)
    run_file(store, datasets, uploads, library, job_id)
    record = store.get(job_id)
    assert (record.state, record.reason) == (JobState.FAILED, "fuseki down")
    assert uploads.saved == {}


def test_a_dataset_that_cannot_be_deleted_leaves_the_state_unchanged(
    store, queue, uploads, datasets, library
):
    class StuckDatasets(FakeDatasetStore):
        def delete(self, name):
            raise RuntimeError("delete refused")

    job_id = submit_file(store, uploads, queue)
    run_file(store, StuckDatasets(), uploads, library, job_id)
    assert store.get(job_id).state is JobState.COMPLETED
    assert uploads.saved == {}


# --- job_status and active_jobs ----------------------------------------------------------------


def test_job_status_returns_the_record(store, queue):
    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    assert jobs.job_status(job_id, job_store=store).state is JobState.QUEUED


def test_job_status_of_an_unknown_job_is_not_found(store):
    with pytest.raises(JobNotFound):
        jobs.job_status("nope", job_store=store)


def test_active_jobs_are_the_queued_and_running_ones(store):
    for job_id, state in (
        ("q", JobState.QUEUED), ("r", JobState.RUNNING), ("c", JobState.COMPLETED),
        ("f", JobState.FAILED),
    ):  # fmt: skip
        store.create(JobRecord(job_id, Source(file="d.ttl"), datetime.now(UTC), state))
    assert {r.id for r in jobs.active_jobs(job_store=store)} == {"q", "r"}


# --- cancel_job --------------------------------------------------------------------------------


def test_cancelling_a_queued_endpoint_job_revokes_it_and_discards_outputs(store, queue, uploads):
    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    jobs.cancel_job(job_id, job_store=store, queue=queue, upload_store=uploads)
    assert store.get(job_id).state is JobState.CANCELLED
    assert queue.cancelled == [job_id]


def test_cancelling_a_queued_file_job_discards_the_upload(store, queue, uploads):
    job_id = submit_file(store, uploads, queue)
    jobs.cancel_job(job_id, job_store=store, queue=queue, upload_store=uploads)
    assert store.get(job_id).state is JobState.CANCELLED
    assert uploads.saved == {}


def test_cancelling_a_running_job_discards_any_outputs(store, queue, uploads):
    job_id = jobs.submit_endpoint_job(URL, (), job_store=store, queue=queue)
    store.set_state(job_id, JobState.RUNNING)
    jobs.cancel_job(job_id, job_store=store, queue=queue, upload_store=uploads)
    assert store.get(job_id).state is JobState.CANCELLED


@pytest.mark.parametrize(
    "state",
    [JobState.COMPLETED, JobState.COMPLETED_WITH_FAILURES, JobState.FAILED, JobState.CANCELLED],
)
def test_a_finished_job_cannot_be_cancelled(state, store, queue, uploads):
    store.create(JobRecord("j", Source(file="d.ttl"), datetime.now(UTC), state))
    with pytest.raises(JobNotCancellable):
        jobs.cancel_job("j", job_store=store, queue=queue, upload_store=uploads)
    assert store.get("j").state is state
    assert queue.cancelled == []


def test_cancelling_an_unknown_job_is_not_found(store, queue, uploads):
    with pytest.raises(JobNotFound):
        jobs.cancel_job("nope", job_store=store, queue=queue, upload_store=uploads)


# --- finished_at: the job store stamps it, once per final state ---------------------------------


@pytest.fixture
def timed_store():
    return InMemoryJobStore(clock=lambda: FINISHED)


def test_a_job_is_not_finished_while_it_is_queued_or_running(timed_store, queue):
    job_id = jobs.submit_endpoint_job(URL, (), job_store=timed_store, queue=queue)
    assert timed_store.get(job_id).finished_at is None

    timed_store.set_state(job_id, JobState.RUNNING)

    assert timed_store.get(job_id).finished_at is None


@pytest.mark.parametrize(
    ("failures", "state"),
    [((), JobState.COMPLETED), (("a failed",), JobState.COMPLETED_WITH_FAILURES)],
)
def test_a_completed_run_is_finished_when_it_ends(timed_store, queue, library, failures, state):
    library.outcome = FingerprintOutcome(
        files={ReportFormat.HTML: (Path("main.html"),)}, failures=failures
    )
    job_id = jobs.submit_endpoint_job(URL, (), job_store=timed_store, queue=queue)

    run_endpoint(timed_store, library, job_id)

    record = timed_store.get(job_id)
    assert (record.state, record.finished_at) == (state, FINISHED)


def test_a_failed_run_is_finished_when_it_ends(timed_store, queue, library):
    library.error = RuntimeError("boom")
    job_id = jobs.submit_endpoint_job(URL, (), job_store=timed_store, queue=queue)

    run_endpoint(timed_store, library, job_id)

    assert timed_store.get(job_id).finished_at == FINISHED


def test_a_submission_the_queue_refused_is_finished_as_failed(timed_store, queue):
    queue.error = QueueUnavailable("down")
    with pytest.raises(QueueUnavailable):
        jobs.submit_endpoint_job(URL, (), job_store=timed_store, queue=queue)

    (record,) = timed_store.list()
    assert (record.state, record.finished_at) == (JobState.FAILED, FINISHED)


def test_a_cancelled_job_is_finished_when_it_is_cancelled(timed_store, queue, uploads):
    job_id = jobs.submit_endpoint_job(URL, (), job_store=timed_store, queue=queue)

    jobs.cancel_job(job_id, job_store=timed_store, queue=queue, upload_store=uploads)

    assert timed_store.get(job_id).finished_at == FINISHED
