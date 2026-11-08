import pytest

from fingerprinter.domain.exceptions import (
    FormatNotAvailable,
    InvalidSource,
    JobNotCancellable,
    JobNotFound,
    QueueUnavailable,
    UnsupportedFileType,
)
from fingerprinter.domain.model import JobState, ReportFormat


def test_unsupported_file_type_carries_the_accepted_types():
    error = UnsupportedFileType("notes.txt", ["ttl", "rdf"])
    assert error.accepted == ("rdf", "ttl")
    assert "notes.txt" in str(error)
    assert "rdf, ttl" in str(error)


def test_job_not_found_names_the_id():
    assert "j1" in str(JobNotFound("j1"))


def test_format_not_available_names_the_job_and_format():
    message = str(FormatNotAvailable("j1", ReportFormat.SHACL))
    assert "j1" in message
    assert "shacl" in message


def test_job_not_cancellable_names_the_state():
    assert "completed" in str(JobNotCancellable("j1", JobState.COMPLETED))


@pytest.mark.parametrize("error", [InvalidSource, QueueUnavailable])
def test_the_other_errors_are_plain_exceptions_with_a_message(error):
    assert str(error("why")) == "why"
