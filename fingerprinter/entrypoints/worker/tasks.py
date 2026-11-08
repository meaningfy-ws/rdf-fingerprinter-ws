"""The Celery tasks of the worker: they run the job services with the bootstrapped dependencies."""

from pathlib import Path

from celery import Celery

from fingerprinter.services import jobs
from fingerprinter.services.ports import ENDPOINT_TASK, FILE_TASK, Services


def register_tasks(celery_app: Celery, services: Services) -> None:
    @celery_app.task(name=ENDPOINT_TASK, shared=False)
    def fingerprint_endpoint(job_id: str, url: str, graphs: list[str]) -> None:
        jobs.run_endpoint_job(
            job_id, url, tuple(graphs), jobs=services.jobs, fingerprinter=services.fingerprinter
        )

    @celery_app.task(name=FILE_TASK, shared=False)
    def fingerprint_file(job_id: str, path: str) -> None:
        jobs.run_file_job(
            job_id,
            Path(path),
            jobs=services.jobs,
            datasets=services.datasets,
            uploads=services.uploads,
            fingerprinter=services.fingerprinter,
        )
