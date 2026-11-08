"""Job use cases: submit, run (in the worker), follow and cancel (design, Algorithm / approach)."""

import logging
import tempfile
import uuid
from collections.abc import Callable, Collection
from datetime import UTC, datetime
from pathlib import Path, PurePath
from typing import IO
from urllib.parse import urlparse

from fingerprinter.domain.exceptions import (
    InvalidSource,
    JobNotCancellable,
    QueueUnavailable,
    UnsupportedFileType,
)
from fingerprinter.domain.model import FingerprintOutcome, JobRecord, JobState, Source
from fingerprinter.services.ports import (
    DatasetStore,
    Fingerprinter,
    JobQueue,
    JobStore,
    UploadStore,
)

logger = logging.getLogger(__name__)

QUEUE_UNAVAILABLE = "queue unavailable"


def _new_record(job_id: str, source: Source) -> JobRecord:
    return JobRecord(id=job_id, source=source, created_at=datetime.now(UTC), state=JobState.QUEUED)


def _fail_submission(job_id: str, jobs: JobStore) -> QueueUnavailable:
    jobs.set_state(job_id, JobState.FAILED, QUEUE_UNAVAILABLE)
    return QueueUnavailable(QUEUE_UNAVAILABLE)


def submit_endpoint_job(
    url: str, graphs: tuple[str, ...], *, jobs: JobStore, queue: JobQueue
) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidSource("Enter an http or https SPARQL endpoint URL.")
    job_id = str(uuid.uuid4())
    jobs.create(_new_record(job_id, Source(endpoint=url, graphs=graphs)))
    try:
        queue.submit_endpoint(job_id, url, graphs)
    except Exception as error:
        logger.error("Queue unavailable for job %s: %s", job_id, error)
        raise _fail_submission(job_id, jobs) from error
    return job_id


def submit_file_job(
    stream: IO[bytes],
    filename: str,
    *,
    supported_extensions: Collection[str],
    jobs: JobStore,
    uploads: UploadStore,
    queue: JobQueue,
) -> str:
    if PurePath(filename).suffix.lstrip(".").lower() not in supported_extensions:
        raise UnsupportedFileType(filename, supported_extensions)
    job_id = str(uuid.uuid4())
    path = uploads.save(job_id, stream, filename)
    jobs.create(_new_record(job_id, Source(file=filename)))
    try:
        queue.submit_file(job_id, path)
    except Exception as error:
        logger.error("Queue unavailable for job %s: %s", job_id, error)
        uploads.discard(job_id)
        raise _fail_submission(job_id, jobs) from error
    return job_id


def _finish(
    jobs: JobStore,
    job_id: str,
    state: JobState,
    reason: str | None = None,
    failures: tuple[str, ...] = (),
) -> None:
    """Record the end of a run, unless a client cancelled the job meanwhile."""
    if jobs.get(job_id).state is JobState.CANCELLED:
        jobs.discard_outputs(job_id)
        return
    jobs.set_state(job_id, state, reason, failures)


def _run(job_id: str, jobs: JobStore, fingerprint: Callable[[Path], FingerprintOutcome]) -> None:
    if jobs.get(job_id).state is JobState.CANCELLED:
        return
    jobs.set_state(job_id, JobState.RUNNING)
    try:
        with tempfile.TemporaryDirectory() as work_folder:
            outcome = fingerprint(Path(work_folder))
            jobs.save_outputs(job_id, outcome)
    except Exception as error:
        logger.error("Job %s failed: %s", job_id, error)
        _finish(jobs, job_id, JobState.FAILED, reason=str(error))
        return
    state = JobState.COMPLETED_WITH_FAILURES if outcome.failures else JobState.COMPLETED
    _finish(jobs, job_id, state, failures=outcome.failures)


def run_endpoint_job(
    job_id: str,
    url: str,
    graphs: tuple[str, ...],
    *,
    jobs: JobStore,
    fingerprinter: Fingerprinter,
) -> None:
    _run(job_id, jobs, lambda folder: fingerprinter.fingerprint(url, graphs, folder))


def run_file_job(
    job_id: str,
    path: Path,
    *,
    jobs: JobStore,
    datasets: DatasetStore,
    uploads: UploadStore,
    fingerprinter: Fingerprinter,
) -> None:
    name = f"fp-{job_id}"

    def fingerprint(folder: Path) -> FingerprintOutcome:
        datasets.create(name)
        datasets.load_file(name, path)
        return fingerprinter.fingerprint(datasets.sparql_url(name), (), folder)

    try:
        _run(job_id, jobs, fingerprint)
    finally:
        try:
            datasets.delete(name)
        except Exception as error:
            logger.warning("Dataset %s could not be deleted: %s", name, error)
        uploads.discard(job_id)


def job_status(job_id: str, *, jobs: JobStore) -> JobRecord:
    return jobs.get(job_id)


def active_jobs(*, jobs: JobStore) -> list[JobRecord]:
    return [record for record in jobs.list() if record.state.is_active]


def cancel_job(job_id: str, *, jobs: JobStore, queue: JobQueue, uploads: UploadStore) -> None:
    record = jobs.get(job_id)
    if not record.state.is_active:
        raise JobNotCancellable(job_id, record.state)
    jobs.set_state(job_id, JobState.CANCELLED)
    queue.cancel(job_id)
    jobs.discard_outputs(job_id)
    if record.source.file:
        uploads.discard(job_id)
