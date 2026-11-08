from pathlib import Path

import pytest
import requests

from fingerprinter.adapters.fuseki import FusekiDatasetStore
from tests.containers import FusekiServer

RESOURCES = Path(__file__).parent.parent / "resources"
MIME_TYPES = {"rdf": "application/rdf+xml", "ttl": "text/turtle", "trix": "application/trix+xml"}
TURTLE = "<http://example.org/s> <http://example.org/p> <http://example.org/o> .\n"
ASK_TRIPLE = "ASK { <http://example.org/s> <http://example.org/p> <http://example.org/o> }"


@pytest.fixture
def datasets(fuseki: FusekiServer) -> FusekiDatasetStore:
    return FusekiDatasetStore(fuseki.url, fuseki.user, fuseki.password, MIME_TYPES)


def ask(datasets: FusekiDatasetStore, name: str, query: str) -> bool:
    response = requests.get(
        datasets.sparql_url(name),
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["boolean"]


def exists(fuseki: FusekiServer, name: str) -> bool:
    response = requests.get(
        f"{fuseki.url}/$/datasets/{name}", auth=(fuseki.user, fuseki.password), timeout=30
    )
    return response.status_code == 200


def test_create_makes_a_dataset_that_answers_queries(datasets, fuseki):
    datasets.create("fp-create")

    assert exists(fuseki, "fp-create")
    assert ask(datasets, "fp-create", "ASK { ?s ?p ?o }") is False
    datasets.delete("fp-create")


def test_create_of_an_existing_dataset_fails(datasets):
    datasets.create("fp-twice")

    with pytest.raises(requests.HTTPError):
        datasets.create("fp-twice")
    datasets.delete("fp-twice")


def test_load_file_uses_the_content_type_of_the_extension(datasets, tmp_path):
    datasets.create("fp-turtle")
    turtle = tmp_path / "data.ttl"
    turtle.write_text(TURTLE)

    datasets.load_file("fp-turtle", turtle)

    assert ask(datasets, "fp-turtle", ASK_TRIPLE) is True
    datasets.delete("fp-turtle")


def test_load_file_loads_an_rdf_xml_file(datasets):
    datasets.create("fp-rdfxml")

    datasets.load_file("fp-rdfxml", RESOURCES / "continents-source-ap.rdf")

    assert ask(datasets, "fp-rdfxml", "ASK { ?s a ?class }") is True
    datasets.delete("fp-rdfxml")


def test_load_file_loads_trix_as_application_trix_xml(datasets, tmp_path):
    datasets.create("fp-trix")
    trix = tmp_path / "data.trix"
    trix.write_text(
        '<?xml version="1.0"?><trix xmlns="http://www.w3.org/2004/03/trix/trix-1/"><graph>'
        "<uri>http://example.org/g</uri><triple><uri>http://example.org/s</uri>"
        "<uri>http://example.org/p</uri><uri>http://example.org/o</uri></triple></graph></trix>"
    )

    datasets.load_file("fp-trix", trix)

    assert ask(datasets, "fp-trix", f"ASK {{ GRAPH ?g {{ {ASK_TRIPLE[5:-1]} }} }}") is True
    datasets.delete("fp-trix")


def test_load_file_of_an_unknown_extension_is_refused(datasets, tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text("hello")

    with pytest.raises(ValueError, match="txt"):
        datasets.load_file("whatever", notes)


def test_load_file_of_malformed_data_fails(datasets, tmp_path):
    datasets.create("fp-malformed")
    broken = tmp_path / "broken.ttl"
    broken.write_text("this is not turtle")

    with pytest.raises(requests.HTTPError):
        datasets.load_file("fp-malformed", broken)
    datasets.delete("fp-malformed")


def test_load_file_into_a_missing_dataset_fails(datasets, tmp_path):
    turtle = tmp_path / "data.ttl"
    turtle.write_text(TURTLE)

    with pytest.raises(requests.HTTPError):
        datasets.load_file("fp-missing", turtle)


def test_delete_removes_the_dataset(datasets, fuseki):
    datasets.create("fp-delete")

    datasets.delete("fp-delete")

    assert not exists(fuseki, "fp-delete")


def test_delete_of_a_missing_dataset_is_not_an_error(datasets):
    datasets.delete("fp-never-created")


def test_wrong_credentials_fail_loudly(fuseki):
    store = FusekiDatasetStore(fuseki.url, fuseki.user, "wrong", MIME_TYPES)

    with pytest.raises(requests.HTTPError):
        store.create("fp-denied")
    with pytest.raises(requests.HTTPError):
        store.delete("fp-denied")


def test_sparql_url_names_the_query_endpoint(datasets, fuseki):
    assert datasets.sparql_url("fp-x") == f"{fuseki.url}/fp-x/sparql"
