"""Report access: list, download and delete the outputs of finished jobs."""

from pathlib import Path

from fingerprinter.domain.model import JobRecord, ReportFormat
from fingerprinter.services.ports import JobStore


def list_reports(*, jobs: JobStore) -> list[JobRecord]:
    return jobs.list()


def report_download(job_id: str, report_format: ReportFormat, *, jobs: JobStore) -> Path:
    """The file to serve; raises ``JobNotFound`` or ``FormatNotAvailable`` (both 404)."""
    return jobs.file_for(job_id, report_format)


def delete_report(job_id: str, *, jobs: JobStore) -> None:
    jobs.delete(job_id)


def delete_all_reports(*, jobs: JobStore) -> None:
    jobs.delete_all()
