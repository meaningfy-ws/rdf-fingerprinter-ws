from fingerprint.domain.profile import Failure

from fingerprinter.adapters.fingerprint_library import describe_failure


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
