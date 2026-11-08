"""The worker's tasks run the job services with the bootstrapped dependencies (design D-6)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from celery import Celery

from fingerprinter.domain.model import JobRecord, JobState, Source
from fingerprinter.entrypoints.worker.tasks import register_tasks
from fingerprinter.services.ports import Services
from tests.fakes import (
    FakeDatasetStore,
    FakeFingerprinter,
    FakeJobQueue,
    FakeUploadStore,
    InMemoryJobStore,
)


class RecordingDatasetStore(FakeDatasetStore):
    def __init__(self) -> None:
        super().__init__()
        self.loaded: list[Path] = []

    def load_file(self, name: str, path: Path) -> None:
        self.loaded.append(path)
        super().load_file(name, path)


@pytest.fixture
def services() -> Services:
    return Services(
        job_store=InMemoryJobStore(),
        upload_store=FakeUploadStore(),
        queue=FakeJobQueue(),
        dataset_store=RecordingDatasetStore(),
        fingerprinter=FakeFingerprinter(),
        supported_extensions=frozenset({"ttl"}),
        output_mime_types={},
    )


@pytest.fixture
def celery_app(services) -> Celery:
    app = Celery("test")
    register_tasks(app, lambda: services)
    return app


def queue_job(services: Services, source: Source) -> None:
    services.job_store.create(
        JobRecord(id="j1", source=source, created_at=datetime.now(UTC), state=JobState.QUEUED)
    )


def test_the_tasks_are_registered_under_the_names_the_queue_sends(celery_app):
    assert {"fingerprint_endpoint", "fingerprint_file"} <= set(celery_app.tasks)


def test_the_endpoint_task_runs_the_job_with_the_graphs_as_a_tuple(celery_app, services):
    queue_job(services, Source(endpoint="http://example.org/sparql", graphs=("http://g",)))

    celery_app.tasks["fingerprint_endpoint"]("j1", "http://example.org/sparql", ["http://g"])

    assert services.fingerprinter.calls == [("http://example.org/sparql", ("http://g",))]
    assert services.job_store.get("j1").state is JobState.COMPLETED


def test_the_file_task_runs_the_job_with_the_path_as_a_path(celery_app, services, tmp_path):
    queue_job(services, Source(file="a.ttl"))
    services.upload_store.saved["j1"] = tmp_path / "a.ttl"

    celery_app.tasks["fingerprint_file"]("j1", str(tmp_path / "a.ttl"))

    assert services.dataset_store.loaded == [tmp_path / "a.ttl"]
    assert services.dataset_store.datasets == {}  # created, loaded and deleted again
    assert services.job_store.get("j1").state is JobState.COMPLETED
