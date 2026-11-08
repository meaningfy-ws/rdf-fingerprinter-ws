"""The Fuseki adapter's errors name the status and never the internal URL (R2-8)."""

import pytest
import requests

from fingerprinter.adapters.fuseki import FusekiDatasetStore

INTERNAL_URL = "http://fuseki-internal:3030"


@pytest.fixture
def store() -> FusekiDatasetStore:
    return FusekiDatasetStore(INTERNAL_URL, "user", "pw", {"ttl": "text/turtle"})


def answer(monkeypatch, method: str, status: int) -> None:
    response = requests.Response()
    response.status_code = status
    response.url = f"{INTERNAL_URL}/$/datasets"
    monkeypatch.setattr(requests, method, lambda *_args, **_kwargs: response)


@pytest.mark.parametrize("call", ["create", "load_file", "delete"])
def test_a_refused_request_raises_an_error_with_the_status_only(store, monkeypatch, tmp_path, call):
    data = tmp_path / "d.ttl"
    data.write_text("x")
    calls = {
        "create": (lambda: store.create("n"), "post"),
        "load_file": (lambda: store.load_file("n", data), "post"),
        "delete": (lambda: store.delete("n"), "delete"),
    }
    action, method = calls[call]
    answer(monkeypatch, method, 500)

    with pytest.raises(requests.HTTPError) as error:
        action()

    assert str(error.value) == "dataset store failed: 500"
