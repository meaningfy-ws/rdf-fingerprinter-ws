"""UI pages: each asks the API and renders what it answers (design U-3, U-4)."""

import io
from collections.abc import Callable
from datetime import UTC, datetime
from http import HTTPStatus
from operator import attrgetter
from typing import Any

import requests
from flask import (
    Flask,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.http import parse_options_header
from werkzeug.wrappers import Response

from fingerprinter.entrypoints.ui import labels
from fingerprinter.entrypoints.ui.api_wrapper import ApiClient
from fingerprinter.entrypoints.ui.forms import FingerprintFileForm, FingerprintSPARQLEndpointForm
from fingerprinter.entrypoints.ui.helpers import FLASH_ERROR, FLASH_SUCCESS
from fingerprinter.entrypoints.ui.presenters import JobView, present, source_name

BYTES_PER_MB = 1024 * 1024
NO_SNIFF = {"X-Content-Type-Options": "nosniff"}
REPORT_HEADERS = NO_SNIFF | {"Content-Security-Policy": "sandbox allow-scripts"}


class ApiError(Exception):
    """The API refused a request or could not be reached; ``sentence`` says so to the user."""

    def __init__(self, sentence: str, status: int | None = None):
        super().__init__(sentence)
        self.sentence = sentence
        self.status = status


def utcnow() -> datetime:
    return datetime.now(UTC)


def _api() -> ApiClient:
    api: ApiClient = current_app.extensions["api"]
    return api


def _upload_limit_mb() -> int:
    limit: int = current_app.config["MAX_UPLOAD_BYTES"]
    return max(1, limit // BYTES_PER_MB)


def _call(name: str, *args: Any) -> Any:
    """Ask the API; an unreachable or refusing API raises ``ApiError``."""
    try:
        response = getattr(_api(), name)(*args)
    except requests.RequestException as error:
        raise ApiError(labels.UNREACHABLE) from error
    if response.status_code >= HTTPStatus.BAD_REQUEST:
        try:
            body = response.json()
        except ValueError:
            body = None
        sentence = labels.problem_sentence(
            body if isinstance(body, dict) else None, upload_limit_mb=_upload_limit_mb()
        )
        raise ApiError(sentence, response.status_code)
    return response


def _job_call(name: str, job_id: str, *args: Any) -> Any:
    """A call about one job: an id the API does not accept is a job it does not have."""
    try:
        return _call(name, job_id, *args)
    except ApiError as error:
        if error.status == HTTPStatus.BAD_REQUEST:
            raise ApiError(labels.PROBLEMS["JobNotFound"], HTTPStatus.NOT_FOUND) from error
        raise


def _error_page(error: ApiError) -> tuple[str, int]:
    status = error.status or HTTPStatus.BAD_GATEWAY
    title = labels.NOT_FOUND_TITLE if status == HTTPStatus.NOT_FOUND else labels.FAILED_TITLE
    return render_template("error.html", title=title, message=error.sentence), status


def _local_path(target: str | None) -> str:
    """``target`` when it is a path on this site, else the Jobs page (no open redirect)."""
    if target and target.startswith("/") and not target.startswith(("//", "/\\")):
        return target
    return url_for("index")


# --- Jobs -----------------------------------------------------------------------------------------


def _filter() -> labels.Filter:
    show = request.args.get("show")
    return next((f for f in labels.FILTERS if f.id == show), labels.FILTERS[0])


def _all_jobs() -> list[JobView]:
    """Every job, newest first."""
    now = utcnow()
    jobs = (present(job, now) for job in _call("get_reports").json())
    return sorted(jobs, key=attrgetter("created_at"), reverse=True)


def _rows_context(chosen: labels.Filter, jobs: list[JobView]) -> dict[str, Any]:
    rows = [job for job in jobs if chosen.states is None or job.state in chosen.states]
    active = [job.id for job in rows if job.active]
    return {
        "show": chosen.id,
        "next_url": url_for("index", show=None if chosen is labels.FILTERS[0] else chosen.id),
        "total": len(jobs),
        "rows": rows,
        "polling": bool(active),
        "was": ",".join(active),
        "paused": False,
        "announce": None,
    }


def index() -> str:
    chosen = _filter()
    try:
        context = _rows_context(chosen, _all_jobs())
    except ApiError as error:
        flash(error.sentence, FLASH_ERROR)
        context = {"show": chosen.id, "total": None}
    return render_template("jobs/index.html", filters=labels.FILTERS, **context)


def job_rows() -> str:
    """The table body, re-fetched by the page while a job is active (design, live status)."""
    chosen, was = _filter(), request.args.get("was", "")
    try:
        jobs = _all_jobs()
    except ApiError:
        context = {"show": chosen.id, "rows": [], "polling": True, "was": was, "paused": True}
        return render_template("jobs/_rows.html", announce="", **context)
    ended = [job for job in jobs if job.id in was.split(",") and not job.active]
    context = _rows_context(chosen, jobs)
    context["announce"] = " ".join(f"{job.source}: {job.label}." for job in ended)
    return render_template("jobs/_rows.html", **context)


# --- New job --------------------------------------------------------------------------------------


def _new_job_page(tab: str, form: Any, status: int = HTTPStatus.OK) -> tuple[str, int]:
    config = current_app.config
    page = render_template(
        "jobs/new.html",
        tab=tab,
        form=form,
        accepted=[f".{extension}" for extension in config["ACCEPTED_EXTENSIONS"]],
        limit_mb=_upload_limit_mb(),
        formats=labels.FORMATS,
    )
    return page, status


def new_job() -> tuple[str, int]:
    if request.args.get("from") == "file":
        return _new_job_page("file", FingerprintFileForm(formdata=None))
    return _new_job_page("endpoint", FingerprintSPARQLEndpointForm(formdata=None))


def _started(form: Any, field: Any, tab: str, *call: Any) -> Response | tuple[str, int]:
    """Start the job; on success back to the console, else the form with the sentence at the field."""
    try:
        _call(*call)
    except ApiError as error:
        field.errors = [error.sentence]
        return _new_job_page(tab, form)
    flash(labels.JOB_STARTED, FLASH_SUCCESS)
    return redirect(url_for("index"))


def start_endpoint_job() -> Response | tuple[str, int]:
    form = FingerprintSPARQLEndpointForm()
    if form.validate_on_submit():
        graphs = (form.graphs.data or "").split()
        return _started(
            form,
            form.sparql_endpoint_url,
            "endpoint",
            "fingerprint_sparql_endpoint",
            form.sparql_endpoint_url.data,
            graphs,
        )
    return _new_job_page("endpoint", form)


def start_file_job() -> Response | tuple[str, int]:
    form = FingerprintFileForm()
    if form.validate_on_submit():
        return _started(form, form.data_file, "file", "fingerprint_file", form.data_file.data)
    return _new_job_page("file", form)


def upload_too_large(_error: Exception) -> tuple[str, int]:
    """The request was cut off at the UI's own limit, before it reached the API."""
    form = FingerprintFileForm(formdata=None)
    form.data_file.errors = [labels.problem_sentence(
        {"type": f"{labels.PROBLEM_TYPE_PREFIX}UploadTooLarge"}, upload_limit_mb=_upload_limit_mb()
    )]  # fmt: skip
    return _new_job_page("file", form, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)


# --- Files and the report -------------------------------------------------------------------------


def _served(response: Any, *, attachment: bool, name: str, headers: dict[str, str]) -> Response:
    """The API's file, as the UI serves it: the name and type are the API's."""
    _, disposition = parse_options_header(response.headers.get("Content-Disposition", ""))
    mimetype, _ = parse_options_header(
        response.headers.get("Content-Type", "")
    )  # Flask adds the charset
    served = send_file(
        io.BytesIO(response.content),
        mimetype=mimetype or None,
        download_name=disposition.get("filename") or name,
        as_attachment=attachment,
    )
    served.headers.update(headers)
    return served


def job_report(job_id: str) -> Response | tuple[str, int]:
    try:
        response = _job_call("get_file", job_id, "html")
    except ApiError as error:
        return _error_page(error)
    return _served(response, attachment=False, name="main.html", headers=REPORT_HEADERS)


def job_download(
    job_id: str, report_format: str, name: str | None = None
) -> Response | tuple[str, int]:
    try:
        response = _job_call("get_file", job_id, report_format, *([name] if name else []))
    except ApiError as error:
        return _error_page(error)
    return _served(response, attachment=True, name=name or report_format, headers=NO_SNIFF)


# --- Delete and cancel ----------------------------------------------------------------------------


def _confirmation(job_id: str, dialog: labels.Confirmation, action: str) -> str | tuple[str, int]:
    try:
        job = _job_call("get_job", job_id).json()
    except ApiError as error:
        return _error_page(error)
    keep = _local_path(request.args.get("next"))
    return render_template(
        "confirm.html",
        dialog=dialog,
        source=source_name(job),
        action=url_for(action, job_id=job_id, next=keep),
        keep=keep,
    )


def confirm_delete(job_id: str) -> str | tuple[str, int]:
    return _confirmation(job_id, labels.DELETE_CONFIRMATION, "delete_job")


def confirm_cancel(job_id: str) -> str | tuple[str, int]:
    return _confirmation(job_id, labels.CANCEL_CONFIRMATION, "cancel_job")


def _acted(call: str, job_id: str, done: str, then: str) -> Response:
    try:
        _job_call(call, job_id)
        flash(done, FLASH_SUCCESS)
    except ApiError as error:
        flash(error.sentence, FLASH_ERROR)
    return redirect(then)


def delete_job(job_id: str) -> Response:
    return _acted("delete_report", job_id, labels.REPORT_DELETED, url_for("index"))


def cancel_job(job_id: str) -> Response:
    then = _local_path(request.args.get("next"))
    return _acted("cancel_task", job_id, labels.JOB_CANCELLED, then)


ROUTES: tuple[tuple[str, Callable[..., Any], tuple[str, ...]], ...] = (
    ("/", index, ("GET",)),
    ("/jobs/rows", job_rows, ("GET",)),
    ("/jobs/new", new_job, ("GET",)),
    ("/jobs/endpoint", start_endpoint_job, ("POST",)),
    ("/jobs/file", start_file_job, ("POST",)),
    ("/jobs/<job_id>/report", job_report, ("GET",)),
    ("/jobs/<job_id>/files/<report_format>", job_download, ("GET",)),
    ("/jobs/<job_id>/files/<report_format>/<name>", job_download, ("GET",)),
    ("/jobs/<job_id>/delete", confirm_delete, ("GET",)),
    ("/jobs/<job_id>/delete", delete_job, ("POST",)),
    ("/jobs/<job_id>/cancel", confirm_cancel, ("GET",)),
    ("/jobs/<job_id>/cancel", cancel_job, ("POST",)),
)


def register(app: Flask) -> None:
    for rule, view, methods in ROUTES:
        app.add_url_rule(rule, view_func=view, methods=list(methods))
    app.register_error_handler(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, upload_too_large)
