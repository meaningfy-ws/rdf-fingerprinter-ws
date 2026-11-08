"""The e2e stack: the bootstrapped API app in-process, a real worker, Fuseki and Redis (design D-11)."""

import importlib
import socket
import sys
import time
from collections.abc import Iterator
from types import ModuleType

import pytest
import requests
from celery.contrib.testing.worker import start_worker

from fingerprinter.domain.model import JobState
from tests.containers import FusekiServer, PlantUmlServer, RedisServer

WAIT_SECONDS = 180
FINAL_STATES = {state for state in JobState if not state.is_active}


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@pytest.fixture(scope="session")
def stack(
    fuseki: FusekiServer, redis_server: RedisServer, plantuml: PlantUmlServer, tmp_path_factory
) -> Iterator[ModuleType]:
    """``fingerprinter.bootstrap`` imported afresh with the environment pointing at the containers."""
    folders = tmp_path_factory.mktemp("e2e")
    (folders / "db").mkdir()
    (folders / "reports").mkdir()
    environment = {
        "RDF_FINGERPRINTER_API_SECRET_KEY": "e2e-api",
        "RDF_FINGERPRINTER_UI_SECRET_KEY": "e2e-ui",
        # the UI talks to the API on this port (design U-12: set before bootstrap is imported)
        "RDF_FINGERPRINTER_API_LOCATION": "http://127.0.0.1",
        "RDF_FINGERPRINTER_API_PORT": str(free_port()),
        "RDF_FINGERPRINTER_REDIS_LOCATION": f"redis://{redis_server.host}",
        "RDF_FINGERPRINTER_REDIS_PORT": str(redis_server.port),
        "RDF_FINGERPRINTER_PLANTUML_LOCATION": f"http://{plantuml.host}",
        "RDF_FINGERPRINTER_PLANTUML_PORT": str(plantuml.port),
        "RDF_FINGERPRINTER_FUSEKI_LOCATION": f"http://{fuseki.host}",
        "RDF_FINGERPRINTER_FUSEKI_PORT": str(fuseki.port),
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


def wait_for(api, job_id: str, states: set[JobState] = FINAL_STATES) -> tuple[dict, float]:
    """Poll the job until it is in one of ``states``; return its status and the seconds waited."""
    started = time.monotonic()
    while time.monotonic() - started < WAIT_SECONDS:
        status = api.get(f"/tasks/{job_id}").json()
        if status["state"] in states:
            return status, time.monotonic() - started
        time.sleep(0.25)
    pytest.fail(f"job {job_id} never reached {sorted(states)}")
