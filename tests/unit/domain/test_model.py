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
    file_extension,
)


def test_report_formats_are_the_outputs_the_diagrams_and_the_zip():
    assert [f.value for f in ReportFormat] == [
        "html", "json", "shacl", "puml", "svg", "pattern", "shex", "pitfalls", "zip",
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


def test_a_job_record_is_frozen_and_starts_with_no_reason_failures_formats_or_files():
    record = JobRecord(
        id="j1",
        source=Source(file="data.ttl"),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        state=JobState.QUEUED,
    )
    assert (record.reason, record.failures, record.formats) == (None, (), ())
    assert (record.finished_at, record.files) == (None, {})
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
        finished_at=datetime(2026, 1, 1, 10, 0, 9, tzinfo=UTC),
        files={ReportFormat.HTML: ("main.html",), ReportFormat.JSON: ("profile.json",)},
    )

    assert record.to_dict() == {
        "id": "j1",
        "source": {"endpoint": "http://example.org/sparql", "graphs": ["http://g"]},
        "created_at": "2026-01-01T10:00:00+00:00",
        "state": "completed_with_failures",
        "reason": None,
        "failures": ["m1 failed"],
        "formats": ["html", "json"],
        "finished_at": "2026-01-01T10:00:09+00:00",
        "files": {"html": ["main.html"], "json": ["profile.json"]},
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


@pytest.mark.parametrize(
    ("name", "extension"),
    [("data.ttl", "ttl"), ("DATA.TTL", "ttl"), ("a.b.rdf", "rdf"), ("noextension", ""), ("x/y.nt", "nt")],
)  # fmt: skip
def test_the_file_extension_is_lower_case_without_the_dot(name, extension):
    assert file_extension(name) == extension


def test_the_status_of_a_job_is_its_id_state_reason_and_failures():
    record = JobRecord(
        id="j1",
        source=Source(file="d.ttl"),
        created_at=datetime(2026, 11, 8, tzinfo=UTC),
        state=JobState.COMPLETED_WITH_FAILURES,
        failures=("m failed",),
    )

    assert record.to_status_dict() == {
        "task_id": "j1",
        "state": "completed_with_failures",
        "reason": None,
        "failures": ["m failed"],
    }


def test_a_record_written_before_finished_at_and_files_existed_still_loads():
    old = {
        "id": "j1",
        "source": {"file": "d.ttl", "graphs": []},
        "created_at": "2026-01-01T10:00:00+00:00",
        "state": "completed",
        "reason": None,
        "failures": [],
        "formats": ["html"],
    }

    record = JobRecord.from_dict(old)

    assert (record.finished_at, record.files) == (None, {})


def test_the_formats_of_a_record_are_the_formats_that_have_files():
    record = JobRecord(
        id="j1",
        source=Source(file="d.ttl"),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        state=JobState.COMPLETED,
        files={ReportFormat.HTML: ("main.html",), ReportFormat.JSON: ()},
    )

    assert record.formats == (ReportFormat.HTML,)


@pytest.mark.parametrize(
    ("state", "stamped"),
    [
        (JobState.QUEUED, False),
        (JobState.RUNNING, False),
        (JobState.COMPLETED, True),
        (JobState.COMPLETED_WITH_FAILURES, True),
        (JobState.FAILED, True),
        (JobState.CANCELLED, True),
    ],
)
def test_a_new_state_stamps_the_finish_time_for_a_final_state_only(state, stamped):
    now = datetime(2026, 1, 1, 10, 5, tzinfo=UTC)
    record = JobRecord(
        id="j1",
        source=Source(file="d.ttl"),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        state=JobState.RUNNING,
        files={ReportFormat.HTML: ("main.html",)},
    )

    changed = record.with_state(state, "why", ("m failed",), now)

    assert (changed.state, changed.reason, changed.failures) == (state, "why", ("m failed",))
    assert changed.finished_at == (now if stamped else None)
    assert changed.files == record.files


def test_the_file_names_of_an_outcome_are_sorted_per_format():
    outcome = FingerprintOutcome(
        files={
            ReportFormat.PUML: (Path("w/b.puml"), Path("w/a.puml")),
            ReportFormat.HTML: (Path("w/main.html"),),
            ReportFormat.JSON: (),
        }
    )

    assert outcome.file_names == {
        ReportFormat.PUML: ("a.puml", "b.puml"),
        ReportFormat.HTML: ("main.html",),
    }
