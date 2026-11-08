"""OpenAPI method handlers: parse the request, call a service, shape the answer (design D-4, D-8)."""

from http import HTTPStatus
from typing import Any

from flask import Response, current_app, send_file
from werkzeug.datastructures import FileStorage

from fingerprinter.domain.model import ReportFormat
from fingerprinter.services import jobs, reports
from fingerprinter.services.ports import Services


def _services() -> Services:
    services: Services = current_app.extensions["fingerprinter"]
    return services


def fingerprint_sparql_endpoint(body: dict[str, Any]) -> tuple[dict[str, str], HTTPStatus]:
    services = _services()
    job_id = jobs.submit_endpoint_job(
        body["sparql_endpoint_url"],
        tuple(body.get("graphs", [])),
        job_store=services.job_store,
        queue=services.queue,
    )
    return {"task_id": job_id}, HTTPStatus.ACCEPTED


def fingerprint_file(data_file: FileStorage) -> tuple[dict[str, str], HTTPStatus]:
    services = _services()
    job_id = jobs.submit_file_job(
        data_file.stream,
        data_file.filename or "",
        supported_extensions=services.supported_extensions,
        job_store=services.job_store,
        upload_store=services.upload_store,
        queue=services.queue,
    )
    return {"task_id": job_id}, HTTPStatus.ACCEPTED


def get_fingerprintings() -> tuple[list[dict[str, Any]], HTTPStatus]:
    records = reports.list_reports(job_store=_services().job_store)
    return [record.to_dict() for record in records], HTTPStatus.OK


def get_fingerprinting(uid: str) -> tuple[dict[str, Any], HTTPStatus]:
    return jobs.job_status(uid, job_store=_services().job_store).to_dict(), HTTPStatus.OK


def get_report_file(uid: str, format: str) -> Response:
    path = reports.report_download(uid, ReportFormat(format), job_store=_services().job_store)
    return send_file(path)


def delete_fingerprinting(uid: str) -> tuple[dict[str, str], HTTPStatus]:
    reports.delete_report(uid, job_store=_services().job_store)
    return {"message": f"Report {uid} deleted."}, HTTPStatus.OK


def delete_all_fingerprintings() -> tuple[dict[str, str], HTTPStatus]:
    reports.delete_all_reports(job_store=_services().job_store)
    return {"message": "All reports deleted."}, HTTPStatus.OK


def get_active_tasks() -> tuple[list[dict[str, Any]], HTTPStatus]:
    return [
        record.to_dict() for record in jobs.active_jobs(job_store=_services().job_store)
    ], HTTPStatus.OK


def get_task_status(task_id: str) -> tuple[dict[str, Any], HTTPStatus]:
    record = jobs.job_status(task_id, job_store=_services().job_store)
    return record.to_status_dict(), HTTPStatus.OK


def stop_running_task(task_id: str) -> tuple[dict[str, str], HTTPStatus]:
    services = _services()
    jobs.cancel_job(
        task_id,
        job_store=services.job_store,
        queue=services.queue,
        upload_store=services.upload_store,
    )
    return {"message": f"Job {task_id} cancelled."}, HTTPStatus.OK
