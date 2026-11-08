"""UI pages: each asks the API and renders what it answers."""

import io
import logging
from collections.abc import Callable
from http import HTTPStatus
from typing import Any

from flask import Flask, current_app, flash, redirect, render_template, send_file, url_for
from werkzeug.http import parse_options_header
from werkzeug.wrappers import Response

from fingerprinter.entrypoints.ui.api_wrapper import ApiClient
from fingerprinter.entrypoints.ui.forms import FingerprintFileForm, FingerprintSPARQLEndpointForm
from fingerprinter.entrypoints.ui.helpers import FLASH_ERROR, FLASH_SUCCESS, error_message

logger = logging.getLogger(__name__)


def _api() -> ApiClient:
    api: ApiClient = current_app.extensions["api"]
    return api


def index() -> str:
    return render_template("index.html", fingerprintings=_api().get_reports().json())


def _started_or_flash(response: Any) -> Response | None:
    """Redirect to the active tasks when the API accepted the job, else flash why it did not."""
    if response.status_code != HTTPStatus.ACCEPTED:
        flash(error_message(response), FLASH_ERROR)
        return None
    flash("fingerprinting successfully started", FLASH_SUCCESS)
    return redirect(url_for("get_active_tasks"))


def fingerprint_sparql_endpoint() -> str | Response:
    form = FingerprintSPARQLEndpointForm()
    if form.validate_on_submit():
        response = _api().fingerprint_sparql_endpoint(
            form.sparql_endpoint_url.data or "", (form.graphs.data or "").split()
        )
        started = _started_or_flash(response)
        if started:
            return started
    return render_template(
        "fingerprint/sparql_endpoint_url.html", form=form, title="Fingerprint SPARQL Endpoint"
    )


def fingerprint_file() -> str | Response:
    form = FingerprintFileForm()
    if form.validate_on_submit():
        started = _started_or_flash(_api().fingerprint_file(form.data_file.data))
        if started:
            return started
    return render_template("fingerprint/file.html", form=form, title="Fingerprint File")


def download_report(job_id: str, report_format: str) -> Response:
    response = _api().get_report(job_id, report_format)
    if response.status_code != HTTPStatus.OK:
        flash(error_message(response), FLASH_ERROR)
        return redirect(url_for("index"))
    _, disposition = parse_options_header(response.headers.get("Content-Disposition", ""))
    name = disposition.get("filename") or report_format
    return send_file(
        io.BytesIO(response.content), download_name=f"{job_id}-{name}", as_attachment=True
    )


def delete_fingerprinting(job_id: str) -> Response:
    response = _api().delete_report(job_id)
    if response.status_code == HTTPStatus.OK:
        flash("fingerprinting successfully deleted", FLASH_SUCCESS)
    else:
        flash(error_message(response), FLASH_ERROR)
    return redirect(url_for("index"))


def get_active_tasks() -> str:
    return render_template("tasks/view_active_tasks.html", tasks=_api().get_active_tasks().json())


def revoke_task(task_id: str) -> Response:
    response = _api().cancel_task(task_id)
    if response.status_code == HTTPStatus.OK:
        flash("Job cancelled.", FLASH_SUCCESS)
    else:
        flash(error_message(response), FLASH_ERROR)
    return redirect(url_for("get_active_tasks"))


ROUTES: tuple[tuple[str, Callable[..., Any], tuple[str, ...]], ...] = (
    ("/", index, ("GET",)),
    ("/fingerprint-sparql-endpoint", fingerprint_sparql_endpoint, ("GET", "POST")),
    ("/fingerprint-file", fingerprint_file, ("GET", "POST")),
    ("/reports/<job_id>/<report_format>", download_report, ("GET",)),
    ("/reports/<job_id>", delete_fingerprinting, ("GET",)),
    ("/tasks", get_active_tasks, ("GET",)),
    ("/revoke-task/<task_id>", revoke_task, ("GET",)),
)


def register(app: Flask) -> None:
    for rule, view, methods in ROUTES:
        app.add_url_rule(rule, view_func=view, methods=list(methods))
