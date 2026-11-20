import pytest
from fingerprint.adapters.exceptions import EndpointUnreachable, PermanentError, QueryTimeout
from fingerprint.domain.profile import Failure

from fingerprinter.adapters.fingerprint_library import (
    GENERATOR_IDS,
    LibraryFingerprinter,
    describe_failure,
)
from fingerprinter.domain.exceptions import GraphListingFailed
from fingerprinter.domain.model import ReportFormat

SECRET_URL = "http://user:secret@example.org/sparql"


def test_every_format_the_library_generates_has_its_generator_id():
    written_by_the_report = {
        ReportFormat.HTML,
        ReportFormat.JSON,
        ReportFormat.ZIP,
        ReportFormat.SVG,
    }  # ZIP: the store; SVG: the worker draws it from the PlantUML files

    assert set(GENERATOR_IDS) == set(ReportFormat) - written_by_the_report
    assert list(GENERATOR_IDS.values()) == ["shacl", "puml", "pattern", "shex", "pitfalls"]


def test_a_failure_is_described_by_its_query_kind_context_and_message():
    failure = Failure(
        query_kind="class_partitions",
        graph="http://example.org/g",
        class_iri="http://example.org/C",
        message="timeout",
    )

    assert (
        describe_failure(failure)
        == "class_partitions failed http://example.org/g http://example.org/C: timeout"
    )


def test_a_failure_without_context_or_message_is_still_described():
    assert describe_failure(Failure(query_kind="graphs")) == "graphs failed"


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (EndpointUnreachable, "the endpoint could not be reached"),
        (QueryTimeout, "the endpoint did not answer in time"),
        (PermanentError, "the endpoint refused the query"),
    ],
)
def test_each_library_error_of_a_listing_is_a_fixed_reason_without_the_url(
    monkeypatch, error, reason
):
    def fail(url, settings):
        raise error(f"failed for {url}")

    monkeypatch.setattr("fingerprinter.adapters.fingerprint_library.list_named_graphs", fail)

    with pytest.raises(GraphListingFailed) as raised:
        LibraryFingerprinter().named_graphs(SECRET_URL)

    assert str(raised.value) == reason
    assert "secret" not in str(raised.value) and "example.org" not in str(raised.value)


def test_an_invalid_url_is_not_mapped_to_a_reason(monkeypatch):
    # the service checks the URL first; a ValueError that gets here is a fault, not a listing failure
    def fail(url, settings):
        raise ValueError("bad")

    monkeypatch.setattr("fingerprinter.adapters.fingerprint_library.list_named_graphs", fail)

    with pytest.raises(ValueError):
        LibraryFingerprinter().named_graphs("not a url")
