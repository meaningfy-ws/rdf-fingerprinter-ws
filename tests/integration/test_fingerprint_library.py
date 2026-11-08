import json
from pathlib import Path

import pytest
import requests
from fingerprint.adapters.exceptions import EndpointUnreachable
from fingerprint.service_layer.handlers import fingerprint_report
from fingerprint.service_layer.representations import generate_representations
from fingerprint.service_layer.settings import resolve_settings

from fingerprinter.adapters.fingerprint_library import LibraryFingerprinter
from fingerprinter.adapters.fuseki import FusekiDatasetStore
from fingerprinter.domain.model import ReportFormat
from tests.containers import FusekiServer

RESOURCES = Path(__file__).parent.parent / "resources"
NAMED_GRAPH = "http://example.org/g1"


@pytest.fixture(scope="module")
def continents_endpoint(fuseki: FusekiServer) -> str:
    """A dataset holding the continents authority table in the default graph."""
    datasets = FusekiDatasetStore(
        fuseki.url, fuseki.user, fuseki.password, {"rdf": "application/rdf+xml"}
    )
    datasets.create("lib-continents")
    datasets.load_file("lib-continents", RESOURCES / "continents-source-ap.rdf")
    return datasets.sparql_url("lib-continents")


@pytest.fixture(scope="module")
def pitfall_endpoint(fuseki: FusekiServer) -> str:
    """A dataset whose default graph uses a class it never declares (check p34_untyped_class)."""
    datasets = FusekiDatasetStore(fuseki.url, fuseki.user, fuseki.password, {"ttl": "text/turtle"})
    datasets.create("lib-pitfall")
    datasets.load_file("lib-pitfall", RESOURCES / "pitfall-untyped-class.ttl")
    return datasets.sparql_url("lib-pitfall")


@pytest.fixture(scope="module")
def continents_outcome(continents_endpoint: str, tmp_path_factory):
    """One run on the continents with every format, shared by the tests that read it."""
    return LibraryFingerprinter().fingerprint(
        continents_endpoint, (), tmp_path_factory.mktemp("run")
    )


@pytest.fixture(scope="module")
def two_graphs_endpoint(fuseki: FusekiServer) -> str:
    """The continents in the default graph and the courts table in a named graph."""
    datasets = FusekiDatasetStore(
        fuseki.url, fuseki.user, fuseki.password, {"rdf": "application/rdf+xml"}
    )
    datasets.create("lib-graphs")
    datasets.load_file("lib-graphs", RESOURCES / "continents-source-ap.rdf")
    requests.post(
        f"{fuseki.url}/lib-graphs/data",
        params={"graph": NAMED_GRAPH},
        data=(RESOURCES / "courts-source-ap.rdf").read_bytes(),
        headers={"Content-Type": "application/rdf+xml"},
        auth=(fuseki.user, fuseki.password),
        timeout=60,
    ).raise_for_status()
    return datasets.sparql_url("lib-graphs")


def profiled_graphs(outcome) -> list[str | None]:
    profile = json.loads(outcome.files[ReportFormat.JSON][0].read_text())
    return [graph.get("graph") for graph in profile["graphs"]]


def test_pattern_shex_and_pitfalls_render_through_generate_representations(
    continents_endpoint, tmp_path
):
    """Settles L-1: the library's docs list only shacl and puml, but all render."""
    settings = resolve_settings(env={}, config={"pitfall_scan": True})
    _, run = fingerprint_report(
        continents_endpoint, tmp_path, settings, formats=(), prefix_list=None
    )

    for name in ("pattern", "shex", "pitfalls"):
        files = generate_representations(run, tmp_path / name, [name])
        assert files, name
        assert all(path.stat().st_size > 0 for path in files), name


def test_an_endpoint_job_writes_all_formats(continents_outcome):
    assert continents_outcome.formats == (
        ReportFormat.HTML,
        ReportFormat.JSON,
        ReportFormat.SHACL,
        ReportFormat.PUML,
        ReportFormat.PATTERN,
        ReportFormat.SHEX,
        ReportFormat.PITFALLS,
    )
    for report_format, paths in continents_outcome.files.items():
        assert all(p.parent.name == report_format.value and p.stat().st_size for p in paths)
    assert continents_outcome.files[ReportFormat.HTML][0].name == "main.html"
    assert continents_outcome.files[ReportFormat.JSON][0].name == "profile.json"
    assert "<html" in continents_outcome.files[ReportFormat.HTML][0].read_text().lower()
    assert continents_outcome.failures == ()


def test_the_pitfall_findings_reach_the_report_page(pitfall_endpoint, tmp_path):
    outcome = LibraryFingerprinter().fingerprint(pitfall_endpoint, (), tmp_path)

    tsv = outcome.files[ReportFormat.PITFALLS][0].read_text()
    assert "p34_untyped_class" in tsv
    assert "p34_untyped_class" in outcome.files[ReportFormat.HTML][0].read_text()


def test_named_graphs_are_profiled_when_none_is_selected(two_graphs_endpoint, tmp_path):
    outcome = LibraryFingerprinter().fingerprint(two_graphs_endpoint, (), tmp_path)

    assert sorted(profiled_graphs(outcome), key=str) == [None, NAMED_GRAPH]


def test_a_selected_graph_restricts_the_profile(two_graphs_endpoint, tmp_path):
    outcome = LibraryFingerprinter().fingerprint(two_graphs_endpoint, (NAMED_GRAPH,), tmp_path)

    assert profiled_graphs(outcome) == [NAMED_GRAPH]


def test_an_unreachable_endpoint_raises_endpoint_unreachable(tmp_path):
    with pytest.raises(EndpointUnreachable):
        LibraryFingerprinter().fingerprint("http://unreachable.invalid/sparql", (), tmp_path)


def test_a_usage_error_raises_value_error(continents_endpoint, tmp_path):
    with pytest.raises(ValueError):
        LibraryFingerprinter().fingerprint("not a url", (), tmp_path)
