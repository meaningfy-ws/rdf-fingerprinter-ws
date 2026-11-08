from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path

import pytest

from fingerprinter.domain.model import (
    FingerprintOutcome,
    JobRecord,
    JobState,
    ReportFormat,
    Source,
)


def test_report_formats_are_the_seven_outputs_and_the_zip():
    assert [f.value for f in ReportFormat] == [
        "html", "json", "shacl", "puml", "pattern", "shex", "pitfalls", "zip",
    ]  # fmt: skip


def test_job_states_are_the_six_of_the_design():
    assert {s.value for s in JobState} == {
        "queued", "running", "completed", "completed_with_failures", "failed", "cancelled",
    }  # fmt: skip


@pytest.mark.parametrize(
    ("state", "active"),
    [
        (JobState.QUEUED, True),
        (JobState.RUNNING, True),
        (JobState.COMPLETED, False),
        (JobState.COMPLETED_WITH_FAILURES, False),
        (JobState.FAILED, False),
        (JobState.CANCELLED, False),
    ],
)
def test_only_queued_and_running_jobs_are_active(state, active):
    assert state.is_active is active


def test_an_endpoint_source_has_no_file():
    source = Source(endpoint="http://example.org/sparql", graphs=("http://g",))
    assert source.file is None
    assert source.graphs == ("http://g",)


def test_a_file_source_has_no_endpoint_and_no_graphs_by_default():
    source = Source(file="data.ttl")
    assert source.endpoint is None
    assert source.graphs == ()


@pytest.mark.parametrize("kwargs", [{}, {"endpoint": "http://x", "file": "f.ttl"}])
def test_a_source_is_exactly_an_endpoint_or_a_file(kwargs):
    with pytest.raises(ValueError, match="endpoint or a file"):
        Source(**kwargs)


def test_a_job_record_is_frozen_and_starts_with_no_reason_failures_or_formats():
    record = JobRecord(
        id="j1",
        source=Source(file="data.ttl"),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        state=JobState.QUEUED,
    )
    assert (record.reason, record.failures, record.formats) == (None, (), ())
    with pytest.raises(FrozenInstanceError):
        record.state = JobState.RUNNING  # type: ignore[misc]


def test_an_outcome_lists_the_formats_that_hold_files():
    outcome = FingerprintOutcome(
        files={
            ReportFormat.HTML: (Path("main.html"),),
            ReportFormat.SHACL: (),
            ReportFormat.JSON: (Path("profile.json"),),
        },
        failures=("m1 failed",),
    )
    assert outcome.formats == (ReportFormat.HTML, ReportFormat.JSON)
    assert outcome.failures == ("m1 failed",)


def test_a_job_record_round_trips_through_its_json_shape():
    record = JobRecord(
        id="j1",
        source=Source(endpoint="http://example.org/sparql", graphs=("http://g",)),
        created_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        state=JobState.COMPLETED_WITH_FAILURES,
        reason=None,
        failures=("m1 failed",),
        formats=(ReportFormat.HTML, ReportFormat.JSON),
    )

    assert record.to_dict() == {
        "id": "j1",
        "source": {"endpoint": "http://example.org/sparql", "graphs": ["http://g"]},
        "created_at": "2026-01-01T10:00:00+00:00",
        "state": "completed_with_failures",
        "reason": None,
        "failures": ["m1 failed"],
        "formats": ["html", "json"],
    }
    assert JobRecord.from_dict(record.to_dict()) == record


def test_a_file_source_serialises_under_the_file_key():
    record = JobRecord(
        id="j2",
        source=Source(file="data.ttl"),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        state=JobState.QUEUED,
    )

    assert record.to_dict()["source"] == {"file": "data.ttl", "graphs": []}
    assert JobRecord.from_dict(record.to_dict()) == record
