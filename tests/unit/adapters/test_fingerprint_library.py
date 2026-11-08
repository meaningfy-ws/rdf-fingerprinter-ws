from fingerprint.domain.profile import Failure

from fingerprinter.adapters.fingerprint_library import GENERATOR_IDS, describe_failure
from fingerprinter.domain.model import ReportFormat


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
