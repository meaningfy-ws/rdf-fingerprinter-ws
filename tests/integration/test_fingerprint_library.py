import json
from pathlib import Path

import pytest
import requests
from bs4 import BeautifulSoup
from fingerprint.adapters.exceptions import EndpointUnreachable
from fingerprint.service_layer.handlers import fingerprint_report
from fingerprint.service_layer.representations import generate_representations
from fingerprint.service_layer.settings import resolve_settings

from fingerprinter.adapters.fingerprint_library import LibraryFingerprinter
from fingerprinter.adapters.fuseki import FusekiDatasetStore
from fingerprinter.domain.exceptions import GraphListingFailed
from fingerprinter.domain.model import ReportFormat
from fingerprinter.entrypoints.ui.presenters import DIAGRAM_PREFIX, SVG_SUFFIX, diagram_choices
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
    assert set(continents_outcome.formats) == set(ReportFormat) - {
        ReportFormat.ZIP,
        ReportFormat.SVG,
    }  # SVG: the worker
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
    # the check id also appears among the clean checks of 3.6.0: assert the finding itself
    page = BeautifulSoup(outcome.files[ReportFormat.HTML][0].read_text(), "html.parser")
    finding = page.select_one(
        '#pitfalls details#pitfall-default-p34_untyped_class a[href="http://example.org/Person"]'
    )
    assert finding is not None


def test_named_graphs_are_profiled_when_none_is_selected(two_graphs_endpoint, tmp_path):
    outcome = LibraryFingerprinter().fingerprint(two_graphs_endpoint, (), tmp_path)

    assert sorted(profiled_graphs(outcome), key=str) == [None, NAMED_GRAPH]


def test_a_selected_graph_restricts_the_profile(two_graphs_endpoint, tmp_path):
    outcome = LibraryFingerprinter().fingerprint(two_graphs_endpoint, (NAMED_GRAPH,), tmp_path)

    assert profiled_graphs(outcome) == [NAMED_GRAPH]


def test_an_unreachable_endpoint_raises_endpoint_unreachable(tmp_path):
    with pytest.raises(EndpointUnreachable):
        LibraryFingerprinter().fingerprint("http://unreachable.invalid/sparql", (), tmp_path)


def test_the_named_graphs_of_an_endpoint_are_listed_sorted(fuseki):
    datasets = FusekiDatasetStore(
        fuseki.url, fuseki.user, fuseki.password, {"rdf": "application/rdf+xml"}
    )
    datasets.create("lib-listing")
    graphs = {"http://example.org/b": "courts", "http://example.org/a": "treaties"}
    for graph, table in graphs.items():
        requests.post(
            f"{fuseki.url}/lib-listing/data",
            params={"graph": graph},
            data=(RESOURCES / f"{table}-source-ap.rdf").read_bytes(),
            headers={"Content-Type": "application/rdf+xml"},
            auth=(fuseki.user, fuseki.password),
            timeout=60,
        ).raise_for_status()

    listed = LibraryFingerprinter().named_graphs(datasets.sparql_url("lib-listing"))

    assert listed == ("http://example.org/a", "http://example.org/b")


def test_the_graphs_of_an_unreachable_endpoint_are_a_listing_failure():
    with pytest.raises(GraphListingFailed, match="could not be reached"):
        LibraryFingerprinter().named_graphs("http://unreachable.invalid/sparql")


def test_a_usage_error_raises_value_error(continents_endpoint, tmp_path):
    with pytest.raises(ValueError):
        LibraryFingerprinter().fingerprint("not a url", (), tmp_path)


def test_the_picker_labels_every_diagram_file_the_library_writes(two_graphs_endpoint, tmp_path):
    """Pins L-1: the UI reads the library's diagram file names; a renamed scheme fails here."""
    outcome = LibraryFingerprinter().fingerprint(two_graphs_endpoint, (), tmp_path)
    names = [path.name for path in outcome.files[ReportFormat.PUML]]
    assert all(name.startswith(DIAGRAM_PREFIX) for name in names), names
    assert len(names) > 2, names  # the whole model and vocabularies of each of two graphs

    chosen = diagram_choices(tuple(name.replace(".puml", SVG_SUFFIX) for name in names))

    assert len(chosen) == len(names)
    whole = [d.label for d in chosen if d.label.startswith("Whole model")]
    assert len(whole) == 2 and all(" — " in label for label in whole), whole  # one per graph
    vocabularies = [d.label for d in chosen if d.label.startswith("Vocabulary: ")]
    assert len(vocabularies) == len(names) - 2
    assert all("diagram" not in label and "--" not in label for label in vocabularies)
    for name in names:  # each vocabulary's name is the one in its file name
        module = name.removesuffix(".puml").partition("--")[2].partition("~")[0]
        assert not module or any(f"Vocabulary: {module}" in label for label in vocabularies), name
