"""The e2e stack: the bootstrapped API app in-process, a real worker, Fuseki and Redis (design D-11)."""

import importlib
import sys
import time
from collections.abc import Iterator
from types import ModuleType

import pytest
import requests
from celery.contrib.testing.worker import start_worker

from tests.containers import FusekiServer

WAIT_SECONDS = 180
FINAL_STATES = {"completed", "completed_with_failures", "failed", "cancelled"}


@pytest.fixture(scope="session")
def stack(fuseki: FusekiServer, redis_url: str, tmp_path_factory) -> Iterator[ModuleType]:
    """``fingerprinter.bootstrap`` imported afresh with the environment pointing at the containers."""
    folders = tmp_path_factory.mktemp("e2e")
    (folders / "db").mkdir()
    (folders / "reports").mkdir()
    redis_location, _, redis_port = redis_url.removesuffix("/0").rpartition(":")
    fuseki_location, _, fuseki_port = fuseki.url.rpartition(":")
    environment = {
        "RDF_FINGERPRINTER_API_SECRET_KEY": "e2e-api",
        "RDF_FINGERPRINTER_UI_SECRET_KEY": "e2e-ui",
        "RDF_FINGERPRINTER_REDIS_LOCATION": redis_location,
        "RDF_FINGERPRINTER_REDIS_PORT": redis_port,
        "RDF_FINGERPRINTER_FUSEKI_LOCATION": fuseki_location,
        "RDF_FINGERPRINTER_FUSEKI_PORT": fuseki_port,
        "RDF_FINGERPRINTER_FUSEKI_USERNAME": fuseki.user,
        "RDF_FINGERPRINTER_FUSEKI_PASSWORD": fuseki.password,
        "RDF_FINGERPRINTER_FILE_DB": str(folders / "db"),
        "RDF_FINGERPRINTER_REPORTS_DB": str(folders / "reports"),
    }
    with pytest.MonkeyPatch.context() as patch:
        for name, value in environment.items():
            patch.setenv(name, value)
        patch.delitem(sys.modules, "fingerprinter.bootstrap", raising=False)
        yield importlib.import_module("fingerprinter.bootstrap")


# module scope: a worker living through the session would take the integration tests' broker messages
@pytest.fixture(scope="module")
def worker(stack: ModuleType) -> Iterator[None]:
    # prefork, so that cancelling a running job terminates a child process as in production
    with start_worker(
        stack.celery_app,
        pool="prefork",
        concurrency=2,
        perform_ping_check=False,
        shutdown_timeout=60,
    ):
        yield


@pytest.fixture(scope="module")
def api(stack: ModuleType, worker: None):
    return stack.api_app().test_client()


@pytest.fixture(scope="session")
def dataset_names(fuseki: FusekiServer):
    def names() -> set[str]:
        response = requests.get(
            f"{fuseki.url}/$/datasets", auth=(fuseki.user, fuseki.password), timeout=30
        )
        return {entry["ds.name"].lstrip("/") for entry in response.json()["datasets"]}

    return names


def wait_for(api, job_id: str, states: set[str] = FINAL_STATES) -> tuple[dict, float]:
    """Poll the job until it is in one of ``states``; return its status and the seconds waited."""
    started = time.monotonic()
    while time.monotonic() - started < WAIT_SECONDS:
        status = api.get(f"/tasks/{job_id}").json()
        if status["state"] in states:
            return status, time.monotonic() - started
        time.sleep(0.25)
    pytest.fail(f"job {job_id} never reached {sorted(states)}")
