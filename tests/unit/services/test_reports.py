from datetime import UTC, datetime
from pathlib import Path

import pytest

from fingerprinter.domain.exceptions import FormatNotAvailable, JobNotFound
from fingerprinter.domain.model import FingerprintOutcome, JobRecord, JobState, ReportFormat, Source
from fingerprinter.services import reports
from tests.fakes import InMemoryJobStore


@pytest.fixture
def store():
    store = InMemoryJobStore()
    for job_id in ("a", "b"):
        store.create(JobRecord(job_id, Source(file="d.ttl"), datetime.now(UTC), JobState.QUEUED))
    store.save_outputs("a", FingerprintOutcome(files={ReportFormat.HTML: (Path("main.html"),)}))
    return store


def test_list_reports_returns_every_job(store):
    assert {r.id for r in reports.list_reports(job_store=store)} == {"a", "b"}


def test_report_download_returns_the_file_of_the_format(store):
    assert reports.report_download("a", ReportFormat.HTML, job_store=store) == Path("main.html")


def test_report_download_of_a_format_with_no_file_is_not_available(store):
    with pytest.raises(FormatNotAvailable):
        reports.report_download("a", ReportFormat.SHACL, job_store=store)


def test_report_download_of_an_unknown_report_is_not_found(store):
    with pytest.raises(JobNotFound):
        reports.report_download("nope", ReportFormat.HTML, job_store=store)


def test_delete_report_removes_the_record_and_its_files(store):
    reports.delete_report("a", job_store=store)
    assert [r.id for r in store.list()] == ["b"]
    assert "a" not in store.outputs


def test_delete_report_of_an_unknown_report_is_not_found(store):
    with pytest.raises(JobNotFound):
        reports.delete_report("nope", job_store=store)


def test_delete_all_reports_empties_the_store_and_is_fine_when_already_empty(store):
    reports.delete_all_reports(job_store=store)
    reports.delete_all_reports(job_store=store)
    assert store.list() == []
