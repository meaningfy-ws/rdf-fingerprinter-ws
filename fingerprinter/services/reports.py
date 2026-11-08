"""Report access: list, download and delete the outputs of finished jobs."""

from pathlib import Path

from fingerprinter.domain.exceptions import FormatNotAvailable, JobIsActive
from fingerprinter.domain.model import JobRecord, ReportFormat
from fingerprinter.services.ports import JobStore


def list_reports(*, job_store: JobStore) -> list[JobRecord]:
    return job_store.list()


def report_download(
    job_id: str, report_format: ReportFormat, name: str | None = None, *, job_store: JobStore
) -> Path:
    """The file to serve; raises ``JobNotFound`` or ``FormatNotAvailable`` (both 404).

    A ``name`` reaches the store only when the job's record lists it.
    """
    if name is not None and name not in job_store.get(job_id).files.get(report_format, ()):
        raise FormatNotAvailable(job_id, report_format)
    return job_store.file_for(job_id, report_format, name)


def delete_report(job_id: str, *, job_store: JobStore) -> None:
    """Delete a finished job; raises ``JobIsActive`` for a queued or running one (409)."""
    state = job_store.get(job_id).state
    if state.is_active:
        raise JobIsActive(job_id, state)
    job_store.delete(job_id)


def delete_all_reports(*, job_store: JobStore) -> None:
    job_store.delete_all()
