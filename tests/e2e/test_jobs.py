"""Jobs end to end: the API app, a real worker, Fuseki and Redis (tasks.md, Test map)."""

import time
from pathlib import Path

from fingerprinter.adapters.fuseki import FusekiDatasetStore
from fingerprinter.domain.model import ReportFormat
from tests.e2e.conftest import wait_for

RESOURCES = Path(__file__).parent.parent / "resources"
SETTLE_SECONDS = 30


def submit_file(api, filename: str) -> str:
    files = {"data_file": (filename, (RESOURCES / filename).read_bytes())}
    response = api.post("/fingerprint-file", files=files)
    assert response.status_code == 202
    return response.json()["task_id"]


def report_duration(name: str, seconds: float) -> None:
    print(f"\nDURATION {name}: {seconds:.1f} s")


def test_an_endpoint_job_writes_all_formats(api, fuseki):
    mime_types = {"rdf": "application/rdf+xml"}
    datasets = FusekiDatasetStore(fuseki.url, fuseki.user, fuseki.password, mime_types)
    datasets.create("e2e-continents")
    datasets.load_file("e2e-continents", RESOURCES / "continents-source-ap.rdf")
    endpoint = datasets.sparql_url("e2e-continents")
    response = api.post("/fingerprint-sparql-endpoint", json={"sparql_endpoint_url": endpoint})
    assert response.status_code == 202

    status, seconds = wait_for(api, response.json()["task_id"])
    report_duration("endpoint job, all formats", seconds)

    assert status["state"] in ("completed", "completed_with_failures"), status
    for report_format in ReportFormat:
        download = api.get(f"/reports/{status['task_id']}/{report_format.value}")
        assert download.status_code == 200, report_format
        assert download.content, report_format


def test_the_dataset_is_removed_after_success(api, dataset_names):
    job_id = submit_file(api, "treaties-source-ap.rdf")

    status, seconds = wait_for(api, job_id)
    report_duration("file job, treaties", seconds)

    assert status["state"] in ("completed", "completed_with_failures"), status
    assert f"fp-{job_id}" not in dataset_names()


def test_an_unreachable_endpoint_fails_the_job(api):
    url = "http://unreachable.invalid/sparql"
    response = api.post("/fingerprint-sparql-endpoint", json={"sparql_endpoint_url": url})

    status, seconds = wait_for(api, response.json()["task_id"])
    report_duration("unreachable endpoint", seconds)

    assert status["state"] == "failed"
    assert "unreachable.invalid" in status["reason"]


def test_a_running_job_can_be_cancelled(api, stack, dataset_names):
    job_id = submit_file(api, "treaties-source-ap.rdf")
    dataset = f"fp-{job_id}"
    deadline = time.monotonic() + SETTLE_SECONDS
    while dataset not in dataset_names():  # the task has created its dataset: it is mid-run
        assert time.monotonic() < deadline, "the job never created its dataset"
        time.sleep(0.1)

    assert api.delete(f"/tasks/{job_id}").status_code == 200

    deadline = time.monotonic() + SETTLE_SECONDS
    while dataset in dataset_names() and time.monotonic() < deadline:
        time.sleep(0.25)
    assert dataset not in dataset_names()
    assert api.get(f"/tasks/{job_id}").json()["state"] == "cancelled"
    assert not (stack.settings.file_db / job_id).exists()
    assert [entry.name for entry in (stack.settings.reports_db / job_id).iterdir()] == ["meta.json"]
