"""``JobQueue`` on Celery: tasks are sent by name, so no adapter imports an entrypoint (D-6)."""

from pathlib import Path

from celery import Celery
from kombu.exceptions import OperationalError

from fingerprinter.domain.exceptions import QueueUnavailable
from fingerprinter.services.ports import ENDPOINT_TASK, FILE_TASK


class CeleryJobQueue:
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app

    def _send(self, task: str, job_id: str, args: list[object]) -> None:
        """Send the task under the job id; only broker errors mean the queue is unavailable."""
        try:
            self.celery_app.send_task(task, args=args, task_id=job_id)
        except (OperationalError, OSError) as error:
            raise QueueUnavailable(str(error)) from error

    def submit_endpoint(self, job_id: str, url: str, graphs: tuple[str, ...]) -> None:
        self._send(ENDPOINT_TASK, job_id, [job_id, url, list(graphs)])

    def submit_file(self, job_id: str, path: Path) -> None:
        self._send(FILE_TASK, job_id, [job_id, str(path)])

    def cancel(self, job_id: str) -> None:
        self.celery_app.control.revoke(job_id, terminate=True)
