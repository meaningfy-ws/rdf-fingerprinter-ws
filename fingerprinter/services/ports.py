"""The ports the services depend on (design D-2); adapters implement them."""

from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Protocol

from fingerprinter.domain.model import FingerprintOutcome, JobRecord, JobState, ReportFormat


class Fingerprinter(Protocol):
    def fingerprint(
        self, endpoint_url: str, graphs: tuple[str, ...], work_folder: Path
    ) -> FingerprintOutcome:
        """Fingerprint the endpoint into ``work_folder``; the outcome names the files written."""
        ...


class DatasetStore(Protocol):
    def create(self, name: str) -> None: ...

    def load_file(self, name: str, path: Path) -> None: ...

    def delete(self, name: str) -> None:
        """Delete the dataset; a missing dataset is not an error."""
        ...

    def sparql_url(self, name: str) -> str: ...


class JobStore(Protocol):
    """Raises ``JobNotFound`` for an unknown id and ``FormatNotAvailable`` when no file exists."""

    def create(self, record: JobRecord) -> None: ...

    def get(self, job_id: str) -> JobRecord: ...

    def list(self) -> list[JobRecord]: ...

    def set_state(
        self,
        job_id: str,
        state: JobState,
        reason: str | None = None,
        failures: tuple[str, ...] = (),
    ) -> None: ...

    def save_outputs(self, job_id: str, outcome: FingerprintOutcome) -> None:
        """Move the outcome's files into the job's report; refuses a job that already has outputs."""
        ...

    def discard_outputs(self, job_id: str) -> None: ...

    def file_for(self, job_id: str, report_format: ReportFormat) -> Path: ...

    def delete(self, job_id: str) -> None: ...

    def delete_all(self) -> None: ...


class UploadStore(Protocol):
    def save(self, job_id: str, stream: IO[bytes], filename: str) -> Path: ...

    def discard(self, job_id: str) -> None: ...


class JobQueue(Protocol):
    def submit_endpoint(self, job_id: str, url: str, graphs: tuple[str, ...]) -> None: ...

    def submit_file(self, job_id: str, path: Path) -> None: ...

    def cancel(self, job_id: str) -> None: ...


# The task names the queue sends and the worker registers; one definition, so they cannot drift.
ENDPOINT_TASK = "fingerprint_endpoint"
FILE_TASK = "fingerprint_file"


@dataclass(frozen=True)
class Services:
    """What the entrypoints call the use cases with: the ports, built once by ``bootstrap``."""

    jobs: JobStore
    uploads: UploadStore
    queue: JobQueue
    datasets: DatasetStore
    fingerprinter: Fingerprinter
    supported_extensions: Collection[str]
