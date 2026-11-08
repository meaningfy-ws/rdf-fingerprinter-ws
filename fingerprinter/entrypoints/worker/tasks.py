"""The Celery tasks of the worker: they run the job services with the bootstrapped dependencies."""

from collections.abc import Callable
from pathlib import Path

from celery import Celery

from fingerprinter.services import jobs
from fingerprinter.services.ports import ENDPOINT_TASK, FILE_TASK, Services


def register_tasks(celery_app: Celery, get_services: Callable[[], Services]) -> None:
    """Register the tasks; ``get_services`` is called when a task runs, not at registration."""

    @celery_app.task(name=ENDPOINT_TASK, shared=False)
    def fingerprint_endpoint(job_id: str, url: str, graphs: list[str]) -> None:
        services = get_services()
        jobs.run_endpoint_job(
            job_id,
            url,
            tuple(graphs),
            job_store=services.job_store,
            fingerprinter=services.fingerprinter,
        )

    @celery_app.task(name=FILE_TASK, shared=False)
    def fingerprint_file(job_id: str, path: str) -> None:
        services = get_services()
        jobs.run_file_job(
            job_id,
            Path(path),
            job_store=services.job_store,
            dataset_store=services.dataset_store,
            upload_store=services.upload_store,
            fingerprinter=services.fingerprinter,
        )
