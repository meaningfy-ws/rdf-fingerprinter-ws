"""OpenAPI method handlers: parse the request, call a service, shape the answer (design D-4, D-8)."""

from typing import Any

from flask import Response, current_app, send_file
from werkzeug.datastructures import FileStorage

from fingerprinter.domain.model import ReportFormat
from fingerprinter.services import jobs, reports
from fingerprinter.services.ports import Services


def _services() -> Services:
    services: Services = current_app.extensions["fingerprinter"]
    return services


def fingerprint_sparql_endpoint(body: dict[str, Any]) -> tuple[dict[str, str], int]:
    services = _services()
    job_id = jobs.submit_endpoint_job(
        body["sparql_endpoint_url"],
        tuple(body.get("graphs", [])),
        jobs=services.jobs,
        queue=services.queue,
    )
    return {"task_id": job_id}, 202


def fingerprint_file(data_file: FileStorage) -> tuple[dict[str, str], int]:
    services = _services()
    job_id = jobs.submit_file_job(
        data_file.stream,
        data_file.filename or "",
        supported_extensions=services.supported_extensions,
        jobs=services.jobs,
        uploads=services.uploads,
        queue=services.queue,
    )
    return {"task_id": job_id}, 202


def get_fingerprintings() -> tuple[list[dict[str, Any]], int]:
    records = reports.list_reports(jobs=_services().jobs)
    return [record.to_dict() for record in records], 200


def get_fingerprinting(uid: str) -> tuple[dict[str, Any], int]:
    return jobs.job_status(uid, jobs=_services().jobs).to_dict(), 200


def get_report_file(uid: str, format: str) -> Response:
    path = reports.report_download(uid, ReportFormat(format), jobs=_services().jobs)
    return send_file(path)


def delete_fingerprinting(uid: str) -> tuple[dict[str, str], int]:
    reports.delete_report(uid, jobs=_services().jobs)
    return {"message": f"Report {uid} deleted."}, 200


def delete_all_fingerprintings() -> tuple[dict[str, str], int]:
    reports.delete_all_reports(jobs=_services().jobs)
    return {"message": "All reports deleted."}, 200


def get_active_tasks() -> tuple[list[dict[str, Any]], int]:
    return [record.to_dict() for record in jobs.active_jobs(jobs=_services().jobs)], 200


def get_task_status(task_id: str) -> tuple[dict[str, Any], int]:
    record = jobs.job_status(task_id, jobs=_services().jobs)
    return {
        "task_id": record.id,
        "state": record.state.value,
        "reason": record.reason,
        "failures": list(record.failures),
    }, 200


def stop_running_task(task_id: str) -> tuple[dict[str, str], int]:
    services = _services()
    jobs.cancel_job(task_id, jobs=services.jobs, queue=services.queue, uploads=services.uploads)
    return {"message": f"Job {task_id} cancelled."}, 200
