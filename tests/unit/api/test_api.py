"""The API's contract: routes, status codes and problem responses, with the fakes behind it."""

import io
from datetime import UTC, datetime
from pathlib import Path

import pytest

from fingerprinter.domain.exceptions import QueueUnavailable, UploadTooLarge
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
J1 = "11111111-1111-4111-8111-111111111111"
J2 = "22222222-2222-4222-8222-222222222222"
UNKNOWN = "99999999-9999-4999-8999-999999999999"


@pytest.fixture
def services() -> Services:
    return Services(
        job_store=InMemoryJobStore(),
        upload_store=FakeUploadStore(),
        queue=FakeJobQueue(),
        dataset_store=FakeDatasetStore(),
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
    services.job_store.create(record)
    return record


def seed_output(services: Services, job_id: str, report_format: ReportFormat, path: Path) -> None:
    services.job_store.outputs.setdefault(job_id, {})[report_format] = (path,)  # type: ignore[attr-defined]


def test_an_endpoint_job_is_accepted_with_a_task_id(client, services):
    response = client.post("/fingerprint-sparql-endpoint", json={"sparql_endpoint_url": ENDPOINT})

    assert response.status_code == 202
    job_id = response.json()["task_id"]
    assert services.job_store.get(job_id).state is JobState.QUEUED
    assert services.queue.submitted == [(job_id, ENDPOINT)]


def test_the_graphs_of_an_endpoint_job_are_kept(client, services):
    body = {"sparql_endpoint_url": ENDPOINT, "graphs": ["http://g1"]}

    job_id = client.post("/fingerprint-sparql-endpoint", json=body).json()["task_id"]

    assert services.job_store.get(job_id).source.graphs == ("http://g1",)


def test_an_invalid_url_is_a_400_problem(client, services):
    response = client.post(
        "/fingerprint-sparql-endpoint", json={"sparql_endpoint_url": "ftp://example.org"}
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["type"] == "urn:fingerprinter:InvalidSource"
    assert "http or https" in response.json()["detail"]
    assert services.job_store.records == {}


def test_an_endpoint_url_with_user_info_is_a_400_problem(client, services):
    response = client.post(
        "/fingerprint-sparql-endpoint",
        json={"sparql_endpoint_url": "https://user:secret@example.org/sparql"},
    )

    assert response.status_code == 400
    assert response.json()["type"] == "urn:fingerprinter:InvalidSource"
    assert "secret" not in response.text
    assert services.job_store.records == {}


def test_a_missing_endpoint_url_is_a_400(client):
    assert client.post("/fingerprint-sparql-endpoint", json={}).status_code == 400


def test_a_supported_file_is_accepted(client, services):
    response = client.post("/fingerprint-file", files={"data_file": ("a.ttl", io.BytesIO(b"x"))})

    assert response.status_code == 202
    assert services.job_store.get(response.json()["task_id"]).source.file == "a.ttl"


def test_an_unsupported_file_is_a_415_problem_listing_the_types(client, services):
    response = client.post("/fingerprint-file", files={"data_file": ("n.txt", io.BytesIO(b"x"))})

    assert response.status_code == 415
    assert response.json()["accepted"] == ["rdf", "ttl"]
    assert services.job_store.records == {}


def test_a_file_over_the_upload_limit_is_a_413_problem_and_no_job(client, services):
    services.upload_store.error = UploadTooLarge("a.ttl", 1024)

    response = client.post("/fingerprint-file", files={"data_file": ("a.ttl", io.BytesIO(b"x"))})

    assert response.status_code == 413
    assert response.json()["type"] == "urn:fingerprinter:UploadTooLarge"
    assert services.job_store.records == {}
    assert services.queue.submitted == []


@pytest.mark.parametrize(
    ("path", "call"),
    [
        ("/fingerprint-sparql-endpoint", lambda c, p: c.post(p, json={"sparql_endpoint_url": ENDPOINT})),
        ("/fingerprint-file", lambda c, p: c.post(p, files={"data_file": ("a.ttl", io.BytesIO(b"x"))})),
    ],
)  # fmt: skip
def test_a_queue_that_is_down_is_a_503_and_the_job_is_failed(client, services, path, call):
    services.queue.error = QueueUnavailable("redis is down")

    response = call(client, path)

    assert response.status_code == 503
    (record,) = services.job_store.records.values()
    assert record.state is JobState.FAILED


def test_reports_lists_the_job_records(client, services):
    seed(services, J1, failures=("m failed",), formats=(ReportFormat.HTML,))
    seed(services, J2, JobState.QUEUED)

    response = client.get("/reports")

    assert response.status_code == 200
    assert [record["id"] for record in response.json()] == [J1, J2]
    assert response.json()[0] == services.job_store.get(J1).to_dict()


def test_a_report_is_its_job_record(client, services):
    seed(services, J1, JobState.FAILED, reason="endpoint unreachable")

    response = client.get(f"/reports/{J1}")

    assert response.status_code == 200
    assert response.json()["state"] == "failed"
    assert response.json()["reason"] == "endpoint unreachable"


@pytest.mark.parametrize(
    "path", ["/reports/not-a-uuid", "/reports/not-a-uuid/html", "/tasks/not-a-uuid"]
)
def test_an_id_that_is_not_a_uuid_is_a_400(client, path):
    assert client.get(path).status_code == 400
    assert client.delete(path.rsplit("/html", 1)[0]).status_code == 400


def test_an_unknown_report_is_a_404_problem(client):
    response = client.get(f"/reports/{UNKNOWN}")

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
    seed(services, J1)
    (tmp_path / name).write_text("content")
    seed_output(services, J1, report_format, tmp_path / name)

    response = client.get(f"/reports/{J1}/{report_format.value}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(content_type)
    assert response.text == "content"


def test_a_format_with_no_file_is_a_404(client, services):
    seed(services, J1)

    assert client.get(f"/reports/{J1}/shacl").status_code == 404


def test_an_unknown_format_is_a_400(client, services):
    seed(services, J1)

    assert client.get(f"/reports/{J1}/docx").status_code == 400


def test_a_format_of_an_unknown_report_is_a_404(client):
    assert client.get(f"/reports/{UNKNOWN}/html").status_code == 404


def test_a_report_is_deleted_once(client, services):
    seed(services, J1)

    assert client.delete(f"/reports/{J1}").status_code == 200
    assert client.delete(f"/reports/{J1}").status_code == 404


@pytest.mark.parametrize("seeded", [[J1, J2], []])
def test_all_reports_are_deleted_even_when_there_are_none(client, services, seeded):
    for job_id in seeded:
        seed(services, job_id)

    response = client.delete("/remove-reports")

    assert response.status_code == 200
    assert services.job_store.records == {}


def test_active_tasks_are_the_queued_and_running_jobs(client, services):
    seed(services, "q", JobState.QUEUED)
    seed(services, "r", JobState.RUNNING)
    seed(services, "c", JobState.COMPLETED)

    response = client.get("/tasks/active")

    assert response.status_code == 200
    assert [record["id"] for record in response.json()] == ["q", "r"]


def test_a_task_status_is_state_reason_and_failures(client, services):
    seed(services, J1, JobState.COMPLETED_WITH_FAILURES, failures=("m failed",))

    response = client.get(f"/tasks/{J1}")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": J1,
        "state": "completed_with_failures",
        "reason": None,
        "failures": ["m failed"],
    }


def test_an_unknown_task_is_a_404(client):
    assert client.get(f"/tasks/{UNKNOWN}").status_code == 404
    assert client.delete(f"/tasks/{UNKNOWN}").status_code == 404


def test_a_queued_task_is_cancelled(client, services):
    seed(services, J1, JobState.QUEUED)

    response = client.delete(f"/tasks/{J1}")

    assert response.status_code == 200
    assert services.job_store.get(J1).state is JobState.CANCELLED
    assert services.queue.cancelled == [J1]


def test_a_finished_task_cannot_be_cancelled(client, services):
    seed(services, J1, JobState.COMPLETED)

    response = client.delete(f"/tasks/{J1}")

    assert response.status_code == 409
    assert response.json()["type"] == "urn:fingerprinter:JobNotCancellable"
    assert services.queue.cancelled == []
