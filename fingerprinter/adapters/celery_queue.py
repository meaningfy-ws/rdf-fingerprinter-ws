"""``JobQueue`` on Celery: tasks are sent by name, so no adapter imports an entrypoint (D-6)."""

from pathlib import Path

from celery import Celery

from fingerprinter.services.ports import ENDPOINT_TASK, FILE_TASK


class CeleryJobQueue:
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app

    def submit_endpoint(self, job_id: str, url: str, graphs: tuple[str, ...]) -> None:
        self.celery_app.send_task(ENDPOINT_TASK, args=[job_id, url, list(graphs)], task_id=job_id)

    def submit_file(self, job_id: str, path: Path) -> None:
        self.celery_app.send_task(FILE_TASK, args=[job_id, str(path)], task_id=job_id)

    def cancel(self, job_id: str) -> None:
        self.celery_app.control.revoke(job_id, terminate=True)
