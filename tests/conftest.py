"""Root test configuration.

Test-type markers (``unit``, ``feature``, ``integration``, ``e2e``) are stamped onto every collected
test by file path in ``pytest_collection_modifyitems``, not by per-file ``pytestmark``: a
``pytestmark`` in a ``conftest.py`` is silently ignored (a conftest is a plugin, not a test
module). The markers are registered in ``pytest.ini``.
"""
from pathlib import Path

import pytest
import requests

from fingerprinter.adapters.sparql_adapter import FusekiSPARQLAdapter, AbstractSPARQLAdapter
from fingerprinter.config import TestingConfig
from fingerprinter.entrypoints.api import app as api_app, connexion_app
from fingerprinter.entrypoints.ui import app as ui_app


class FakeRequests:
    def __init__(self):
        self.text = None
        self.status_code = None
        self.url = None

    def get(self, url, **kwargs):
        self.url = url
        return self

    def post(self, url, data=None, json=None, **kwargs):
        self.url = url
        return self

    def json(self):
        return self.text


class FakeSPARQLAdapter(AbstractSPARQLAdapter):
    def __init__(self, fuseki_service_location: str, requests: requests):
        self.fuseki_service_location = fuseki_service_location
        self.requests = requests
        self.actions = list()

    def create_dataset(self, dataset_name: str):
        self.actions.append(('CREATE', dataset_name))

    def delete_dataset(self, dataset_name: str):
        self.actions.append(('DELETE', dataset_name))

    def get_dataset(self, dataset_name: str) -> dict:
        self.actions.append(('GET', dataset_name))
        return {'name': dataset_name}

    def upload_file(self, dataset_name: str, file_path: str):
        self.actions.append(('UPLOAD', (dataset_name, file_path)))


@pytest.fixture(scope='function')
def fake_requests():
    return FakeRequests()


# used for testing the adapter
def helper_sparql_wrapper(triplestore_service_url: str = "http://localhost:3030",
                          http_client=FakeRequests()):
    return FusekiSPARQLAdapter(triplestore_service_url=triplestore_service_url,
                               http_client=http_client)


# used for testing the services where the adapter is used
@pytest.fixture(scope='function')
def fake_sparql_adapter():
    return FakeSPARQLAdapter('http://localhost:3030', requests)


@pytest.fixture
def api_client():
    api_app.config.from_object(TestingConfig())
    return connexion_app.test_client()


@pytest.fixture
def ui_client():
    ui_app.config.from_object(TestingConfig())
    return ui_app.test_client()


@pytest.fixture(scope="session")
def scenario_context():
    return {}


TESTS_ROOT_DIR = Path(__file__).parent

# The first directory that starts a test's path below tests/ gives its marker.
_MARKERS_BY_DIR = (("unit/", "unit"), ("feature/", "feature"), ("integration/", "integration"), ("e2e/", "e2e"))


def marker_for_path(path: str) -> str | None:
    """The marker implied by the directory a test file lives in, matched below ``tests/`` only."""
    try:
        relative = Path(path).relative_to(TESTS_ROOT_DIR).as_posix()
    except ValueError:
        return None
    return next((marker for directory, marker in _MARKERS_BY_DIR if relative.startswith(directory)), None)


def pytest_collection_modifyitems(items: list) -> None:
    """Stamp each collected test with the marker of its directory."""
    for item in items:
        marker = marker_for_path(str(item.path))
        if marker:
            item.add_marker(getattr(pytest.mark, marker))
