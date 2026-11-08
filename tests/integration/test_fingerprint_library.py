import json
from pathlib import Path

import pytest
import requests
from fingerprint.adapters.exceptions import EndpointUnreachable

from fingerprinter.adapters.fingerprint_library import LibraryFingerprinter
from fingerprinter.adapters.fuseki import FusekiDatasetStore
from fingerprinter.domain.model import ReportFormat
from tests.integration.conftest import FusekiServer

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


def test_an_endpoint_job_writes_the_report_page_and_the_profile(continents_endpoint, tmp_path):
    outcome = LibraryFingerprinter().fingerprint(continents_endpoint, (), tmp_path)

    assert outcome.formats == (ReportFormat.HTML, ReportFormat.JSON)
    assert outcome.files[ReportFormat.HTML] == (tmp_path / "html" / "main.html",)
    assert outcome.files[ReportFormat.JSON] == (tmp_path / "json" / "profile.json",)
    assert "<html" in outcome.files[ReportFormat.HTML][0].read_text().lower()
    assert (
        json.loads(outcome.files[ReportFormat.JSON][0].read_text())["endpoint"]
        == continents_endpoint
    )
    assert outcome.failures == ()


def test_no_selected_graph_profiles_every_graph(two_graphs_endpoint, tmp_path):
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
