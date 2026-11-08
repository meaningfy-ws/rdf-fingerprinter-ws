"""Job use cases: submit, run (in the worker), follow and cancel (design, Algorithm / approach)."""

import logging
import tempfile
import uuid
from collections.abc import Callable, Collection
from datetime import UTC, datetime
from pathlib import Path
from typing import IO
from urllib.parse import urlparse

from fingerprinter.domain.exceptions import (
    DiagramRenderFailed,
    DiagramServerUnavailable,
    InvalidSource,
    JobNotCancellable,
    QueueUnavailable,
    UnsupportedFileType,
)
from fingerprinter.domain.model import (
    FingerprintOutcome,
    JobRecord,
    JobState,
    ReportFormat,
    Source,
    file_extension,
)
from fingerprinter.services.ports import (
    DatasetStore,
    DiagramRenderer,
    Fingerprinter,
    JobQueue,
    JobStore,
    UploadStore,
)

logger = logging.getLogger(__name__)

QUEUE_UNAVAILABLE = "queue unavailable"


def dataset_name(job_id: str) -> str:
    """The name of the temporary dataset a file job loads its upload into."""
    return f"fp-{job_id}"


def _new_record(job_id: str, source: Source) -> JobRecord:
    return JobRecord(id=job_id, source=source, created_at=datetime.now(UTC), state=JobState.QUEUED)


def _fail_submission(job_id: str, job_store: JobStore) -> QueueUnavailable:
    job_store.set_state(job_id, JobState.FAILED, QUEUE_UNAVAILABLE)
    return QueueUnavailable(QUEUE_UNAVAILABLE)


def submit_endpoint_job(
    url: str, graphs: tuple[str, ...], *, job_store: JobStore, queue: JobQueue
) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidSource("Enter an http or https SPARQL endpoint URL.")
    if parsed.username is not None or parsed.password is not None:
        # records are readable by every client: credentials in the URL would leak
        raise InvalidSource("The endpoint URL must not contain a user name or password.")
    job_id = str(uuid.uuid4())
    job_store.create(_new_record(job_id, Source(endpoint=url, graphs=graphs)))
    try:
        queue.submit_endpoint(job_id, url, graphs)
    except QueueUnavailable as error:
        logger.error("Queue unavailable for job %s: %s", job_id, error)
        raise _fail_submission(job_id, job_store) from error
    return job_id


def submit_file_job(
    stream: IO[bytes],
    filename: str,
    *,
    supported_extensions: Collection[str],
    job_store: JobStore,
    upload_store: UploadStore,
    queue: JobQueue,
) -> str:
    if file_extension(filename) not in supported_extensions:
        raise UnsupportedFileType(filename, supported_extensions)
    job_id = str(uuid.uuid4())
    path = upload_store.save(job_id, stream, filename)
    job_store.create(_new_record(job_id, Source(file=filename)))
    try:
        queue.submit_file(job_id, path)
    except QueueUnavailable as error:
        logger.error("Queue unavailable for job %s: %s", job_id, error)
        upload_store.discard(job_id)
        raise _fail_submission(job_id, job_store) from error
    return job_id


def _finish(
    job_store: JobStore,
    job_id: str,
    state: JobState,
    reason: str | None = None,
    failures: tuple[str, ...] = (),
) -> None:
    """Record the end of a run, unless a client cancelled the job meanwhile."""
    if job_store.get(job_id).state is JobState.CANCELLED:
        job_store.discard_outputs(job_id)
        return
    job_store.set_state(job_id, state, reason, failures)


def _start(job_id: str, job_store: JobStore) -> bool:
    """Take the job from queued to running; a duplicate delivery or a cancelled job is left alone."""
    state = job_store.get(job_id).state
    if state is not JobState.QUEUED:
        logger.warning("Job %s is %s, not queued: not run", job_id, state)
        return False
    job_store.set_state(job_id, JobState.RUNNING)
    return True


def _drawn(source: Path, renderer: DiagramRenderer) -> bytes:
    try:
        text = source.read_bytes().decode()
    except UnicodeDecodeError as error:
        raise DiagramRenderFailed("the PlantUML file is not text") from error
    return renderer.render(text)


def _with_diagrams(
    outcome: FingerprintOutcome, renderer: DiagramRenderer, work_folder: Path
) -> FingerprintOutcome:
    """The outcome plus an SVG for every PlantUML file; one that cannot be drawn is a failure.

    Once the server is unreachable or too slow, the remaining diagrams fail with the same cause
    without being tried: each would wait out the timeout.
    """
    folder = work_folder / ReportFormat.SVG.value
    drawn: list[Path] = []
    failures = list(outcome.failures)
    server_down: DiagramServerUnavailable | None = None
    for source in outcome.files.get(ReportFormat.PUML, ()):
        try:
            if server_down:
                raise server_down
            svg = _drawn(source, renderer)
        except DiagramRenderFailed as error:
            server_down = error if isinstance(error, DiagramServerUnavailable) else server_down
            logger.warning("Class diagram %s could not be drawn: %s", source.stem, error)
            failures.append(f"Class diagram {source.stem} could not be drawn: {error}")
            continue
        folder.mkdir(exist_ok=True)
        drawn.append(folder / f"{source.stem}.svg")
        drawn[-1].write_bytes(svg)
    files = {**outcome.files, ReportFormat.SVG: tuple(drawn)} if drawn else outcome.files
    return FingerprintOutcome(files=files, failures=tuple(failures))


def _run(
    job_id: str,
    job_store: JobStore,
    fingerprint: Callable[[Path], FingerprintOutcome],
    renderer: DiagramRenderer,
    clean_up: Callable[[], None] = lambda: None,
) -> None:
    """Run the job, clean up, and only then record how it ended (clients poll that state)."""
    state, reason = JobState.FAILED, None
    failures: tuple[str, ...] = ()
    try:
        with tempfile.TemporaryDirectory() as work_folder:
            outcome = _with_diagrams(fingerprint(Path(work_folder)), renderer, Path(work_folder))
            job_store.save_outputs(job_id, outcome)
        failures = outcome.failures
        state = JobState.COMPLETED_WITH_FAILURES if failures else JobState.COMPLETED
    except Exception as error:
        logger.error("Job %s failed: %s", job_id, error)
        job_store.discard_outputs(job_id)
        reason = str(error)
    finally:
        clean_up()
    _finish(job_store, job_id, state, reason, failures)


def run_endpoint_job(
    job_id: str,
    url: str,
    graphs: tuple[str, ...],
    *,
    job_store: JobStore,
    fingerprinter: Fingerprinter,
    diagram_renderer: DiagramRenderer,
) -> None:
    if _start(job_id, job_store):
        _run(
            job_id,
            job_store,
            lambda folder: fingerprinter.fingerprint(url, graphs, folder),
            diagram_renderer,
        )


def run_file_job(
    job_id: str,
    path: Path,
    *,
    job_store: JobStore,
    dataset_store: DatasetStore,
    upload_store: UploadStore,
    fingerprinter: Fingerprinter,
    diagram_renderer: DiagramRenderer,
) -> None:
    if not _start(job_id, job_store):
        return
    name = dataset_name(job_id)

    def fingerprint(folder: Path) -> FingerprintOutcome:
        dataset_store.create(name)
        dataset_store.load_file(name, path)
        return fingerprinter.fingerprint(dataset_store.sparql_url(name), (), folder)

    def clean_up() -> None:
        try:
            dataset_store.delete(name)
        except Exception as error:
            logger.warning("Dataset %s could not be deleted: %s", name, error)
        upload_store.discard(job_id)

    _run(job_id, job_store, fingerprint, diagram_renderer, clean_up)


def job_status(job_id: str, *, job_store: JobStore) -> JobRecord:
    return job_store.get(job_id)


def active_jobs(*, job_store: JobStore) -> list[JobRecord]:
    return [record for record in job_store.list() if record.state.is_active]


def cancel_job(
    job_id: str, *, job_store: JobStore, queue: JobQueue, upload_store: UploadStore
) -> None:
    record = job_store.get(job_id)
    if not record.state.is_active:
        raise JobNotCancellable(job_id, record.state)
    job_store.set_state(job_id, JobState.CANCELLED)
    queue.cancel(job_id)
    job_store.discard_outputs(job_id)
    if record.source.file:
        upload_store.discard(job_id)
