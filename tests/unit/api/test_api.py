"""The API's contract: routes, status codes and problem responses, with the fakes behind it."""

import io
from datetime import UTC, datetime
from pathlib import Path

import pytest

from fingerprinter.domain.model import JobRecord, JobState, ReportFormat, Source
from fingerprinter.entrypoints.api import create_app
from fingerprinter.services.ports import Services
from tests.fakes import (
    FakeDatasetStore,
    FakeFingerprinter,
    FakeJobQueue,
    FakeUploadStore,
    InMemoryJobStore,
)

ENDPOINT = "http://example.org/sparql"


@pytest.fixture
def services() -> Services:
    return Services(
        jobs=InMemoryJobStore(),
        uploads=FakeUploadStore(),
        queue=FakeJobQueue(),
        datasets=FakeDatasetStore(),
        fingerprinter=FakeFingerprinter(),
        supported_extensions=frozenset({"ttl", "rdf"}),
    )


@pytest.fixture
def client(services):
    return create_app(services).test_client()


def seed(
    services: Services, job_id: str, state: JobState = JobState.COMPLETED, **record_fields
) -> JobRecord:
    record = JobRecord(
        id=job_id,
        source=Source(endpoint=ENDPOINT),
        created_at=datetime(2026, 11, 8, tzinfo=UTC),
        state=state,
        **record_fields,
    )
    services.jobs.create(record)
    return record


def seed_output(services: Services, job_id: str, report_format: ReportFormat, path: Path) -> None:
    services.jobs.outputs.setdefault(job_id, {})[report_format] = (path,)  # type: ignore[attr-defined]


def test_an_endpoint_job_is_accepted_with_a_task_id(client, services):
    response = client.post("/fingerprint-sparql-endpoint", json={"sparql_endpoint_url": ENDPOINT})

    assert response.status_code == 202
    job_id = response.json()["task_id"]
    assert services.jobs.get(job_id).state is JobState.QUEUED
    assert services.queue.submitted == [(job_id, ENDPOINT)]


def test_the_graphs_of_an_endpoint_job_are_kept(client, services):
    body = {"sparql_endpoint_url": ENDPOINT, "graphs": ["http://g1"]}

    job_id = client.post("/fingerprint-sparql-endpoint", json=body).json()["task_id"]

    assert services.jobs.get(job_id).source.graphs == ("http://g1",)


def test_an_invalid_url_is_a_400_problem(client, services):
    response = client.post(
        "/fingerprint-sparql-endpoint", json={"sparql_endpoint_url": "ftp://example.org"}
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["type"] == "urn:fingerprinter:InvalidSource"
    assert "http or https" in response.json()["detail"]
    assert services.jobs.records == {}


def test_a_missing_endpoint_url_is_a_400(client):
    assert client.post("/fingerprint-sparql-endpoint", json={}).status_code == 400


def test_a_supported_file_is_accepted(client, services):
    response = client.post("/fingerprint-file", files={"data_file": ("a.ttl", io.BytesIO(b"x"))})

    assert response.status_code == 202
    assert services.jobs.get(response.json()["task_id"]).source.file == "a.ttl"


def test_an_unsupported_file_is_a_415_problem_listing_the_types(client, services):
    response = client.post("/fingerprint-file", files={"data_file": ("n.txt", io.BytesIO(b"x"))})

    assert response.status_code == 415
    assert response.json()["accepted"] == ["rdf", "ttl"]
    assert services.jobs.records == {}


@pytest.mark.parametrize(
    ("path", "call"),
    [
        ("/fingerprint-sparql-endpoint", lambda c, p: c.post(p, json={"sparql_endpoint_url": ENDPOINT})),
        ("/fingerprint-file", lambda c, p: c.post(p, files={"data_file": ("a.ttl", io.BytesIO(b"x"))})),
    ],
)  # fmt: skip
def test_a_queue_that_is_down_is_a_503_and_the_job_is_failed(client, services, path, call):
    services.queue.error = ConnectionError("redis is down")

    response = call(client, path)

    assert response.status_code == 503
    (record,) = services.jobs.records.values()
    assert record.state is JobState.FAILED


def test_reports_lists_the_job_records(client, services):
    seed(services, "j1", failures=("m failed",), formats=(ReportFormat.HTML,))
    seed(services, "j2", JobState.QUEUED)

    response = client.get("/reports")

    assert response.status_code == 200
    assert [record["id"] for record in response.json()] == ["j1", "j2"]
    assert response.json()[0] == services.jobs.get("j1").to_dict()


def test_a_report_is_its_job_record(client, services):
    seed(services, "j1", JobState.FAILED, reason="endpoint unreachable")

    response = client.get("/reports/j1")

    assert response.status_code == 200
    assert response.json()["state"] == "failed"
    assert response.json()["reason"] == "endpoint unreachable"


def test_an_unknown_report_is_a_404_problem(client):
    response = client.get("/reports/nope")

    assert response.status_code == 404
    assert response.json()["type"] == "urn:fingerprinter:JobNotFound"


@pytest.mark.parametrize(
    ("report_format", "name", "content_type"),
    [
        (ReportFormat.HTML, "main.html", "text/html"),
        (ReportFormat.JSON, "profile.json", "application/json"),
        (ReportFormat.ZIP, "report.zip", "application/zip"),
    ],
)
def test_a_format_is_served_as_a_file(
    client, services, tmp_path, report_format, name, content_type
):
    seed(services, "j1")
    (tmp_path / name).write_text("content")
    seed_output(services, "j1", report_format, tmp_path / name)

    response = client.get(f"/reports/j1/{report_format.value}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(content_type)
    assert response.text == "content"


def test_a_format_with_no_file_is_a_404(client, services):
    seed(services, "j1")

    assert client.get("/reports/j1/shacl").status_code == 404


def test_an_unknown_format_is_a_400(client, services):
    seed(services, "j1")

    assert client.get("/reports/j1/docx").status_code == 400


def test_a_format_of_an_unknown_report_is_a_404(client):
    assert client.get("/reports/nope/html").status_code == 404


def test_a_report_is_deleted_once(client, services):
    seed(services, "j1")

    assert client.delete("/reports/j1").status_code == 200
    assert client.delete("/reports/j1").status_code == 404


@pytest.mark.parametrize("seeded", [["j1", "j2"], []])
def test_all_reports_are_deleted_even_when_there_are_none(client, services, seeded):
    for job_id in seeded:
        seed(services, job_id)

    response = client.delete("/remove-reports")

    assert response.status_code == 200
    assert services.jobs.records == {}


def test_active_tasks_are_the_queued_and_running_jobs(client, services):
    seed(services, "q", JobState.QUEUED)
    seed(services, "r", JobState.RUNNING)
    seed(services, "c", JobState.COMPLETED)

    response = client.get("/tasks/active")

    assert response.status_code == 200
    assert [record["id"] for record in response.json()] == ["q", "r"]


def test_a_task_status_is_state_reason_and_failures(client, services):
    seed(services, "j1", JobState.COMPLETED_WITH_FAILURES, failures=("m failed",))

    response = client.get("/tasks/j1")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "j1",
        "state": "completed_with_failures",
        "reason": None,
        "failures": ["m failed"],
    }


def test_an_unknown_task_is_a_404(client):
    assert client.get("/tasks/nope").status_code == 404
    assert client.delete("/tasks/nope").status_code == 404


def test_a_queued_task_is_cancelled(client, services):
    seed(services, "j1", JobState.QUEUED)

    response = client.delete("/tasks/j1")

    assert response.status_code == 200
    assert services.jobs.get("j1").state is JobState.CANCELLED
    assert services.queue.cancelled == ["j1"]


def test_a_finished_task_cannot_be_cancelled(client, services):
    seed(services, "j1", JobState.COMPLETED)

    response = client.delete("/tasks/j1")

    assert response.status_code == 409
    assert response.json()["type"] == "urn:fingerprinter:JobNotCancellable"
    assert services.queue.cancelled == []
