"""The browser stack: the API and the UI as real servers in threads, a real worker, Chromium (design U-12)."""

import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType
from urllib.parse import urlsplit

import pytest
import requests
import uvicorn
from playwright.sync_api import Browser, Page, sync_playwright
from werkzeug.serving import make_server

from fingerprinter.adapters.fuseki import FusekiDatasetStore
from tests.containers import FusekiServer
from tests.e2e.conftest import wait_for

RESOURCES = Path(__file__).parents[2] / "resources"
AXE = Path(__file__).with_name("axe.min.js")
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]
DESKTOP = {"width": 1280, "height": 800}
SERVER_WAIT_SECONDS = 30
UNREACHABLE = "http://unreachable.invalid/{}"


def _start(target: Callable[[], None], is_up: Callable[[], bool]) -> threading.Thread:
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    deadline = time.monotonic() + SERVER_WAIT_SECONDS
    while not is_up():
        assert time.monotonic() < deadline, "a server did not start"
        time.sleep(0.05)
    return thread


@pytest.fixture(scope="module")
def ui_url(stack: ModuleType, worker: None) -> Iterator[str]:
    """The UI's address; the API it talks to (the port in the settings) runs beside it."""
    api_port = urlsplit(stack.settings.api_url).port
    api = uvicorn.Server(
        uvicorn.Config(stack.api_app(), host="127.0.0.1", port=api_port, log_level="warning")
    )
    api_thread = _start(api.run, lambda: api.started)
    ui = make_server("127.0.0.1", 0, stack.ui_app(), threaded=True)
    ui_thread = _start(ui.serve_forever, lambda: True)
    yield f"http://127.0.0.1:{ui.server_port}"
    ui.shutdown()
    api.should_exit = True
    api_thread.join(SERVER_WAIT_SECONDS)
    ui_thread.join(SERVER_WAIT_SECONDS)


@pytest.fixture(scope="module")
def api_url(stack: ModuleType, ui_url: str) -> str:
    return stack.settings.api_url


@pytest.fixture(scope="module")
def tag(request: pytest.FixtureRequest) -> str:
    """Names this module's jobs and dataset: the job store is shared, so rows must not collide."""
    return request.module.__name__.rsplit(".", 1)[-1].replace("_", "-")


@pytest.fixture(scope="module")
def continents_endpoint(fuseki: FusekiServer, tag: str) -> str:
    datasets = FusekiDatasetStore(
        fuseki.url, fuseki.user, fuseki.password, {"rdf": "application/rdf+xml"}
    )
    datasets.create(f"ui-continents-{tag}")
    datasets.load_file(f"ui-continents-{tag}", RESOURCES / "continents-source-ap.rdf")
    return datasets.sparql_url(f"ui-continents-{tag}")


@pytest.fixture(scope="module")
def start_job(api_url: str) -> Callable[[str], str]:
    """Start an endpoint job through the API; return its id."""

    def start(endpoint: str) -> str:
        response = requests.post(
            f"{api_url}/fingerprint-sparql-endpoint", json={"sparql_endpoint_url": endpoint}
        )
        assert response.status_code == 202, response.text
        return str(response.json()["task_id"])

    return start


@pytest.fixture(scope="module")
def finished_source(tag: str) -> str:
    return UNREACHABLE.format(f"{tag}-finished")


@pytest.fixture(scope="module")
def finished_job(api_url: str, start_job: Callable[[str], str], finished_source: str) -> str:
    """A job in a final state, quickly: its endpoint does not exist."""
    job_id = start_job(finished_source)
    wait_for(_Api(api_url), job_id)
    return job_id


class _Api:
    """What ``wait_for`` needs of a client: ``get(path).json()``."""

    def __init__(self, base: str):
        self.base = base

    def get(self, path: str) -> requests.Response:
        return requests.get(self.base + path, timeout=30)


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch()
        yield chromium
        chromium.close()


@pytest.fixture
def open_page(browser: Browser) -> Iterator[Callable[..., Page]]:
    """``open_page(color_scheme="light", viewport=DESKTOP)``: a fresh page; closed after the test."""
    contexts = []

    def open_(color_scheme: str = "light", viewport: dict | None = None) -> Page:
        context = browser.new_context(color_scheme=color_scheme, viewport=viewport or DESKTOP)
        contexts.append(context)
        return context.new_page()

    yield open_
    for context in contexts:
        context.close()


def axe_violations(page: Page) -> list[dict]:
    """Run axe-core (vendored) on the page with the WCAG 2.2 AA tags; the violations, trimmed."""
    page.add_script_tag(content=AXE.read_text(encoding="utf-8"))
    result = page.evaluate(
        "tags => axe.run(document, {runOnly: {type: 'tag', values: tags}})", AXE_TAGS
    )
    return [
        {
            "id": violation["id"],
            "impact": violation["impact"],
            "targets": [node["target"] for node in violation["nodes"]],
        }
        for violation in result["violations"]
    ]
