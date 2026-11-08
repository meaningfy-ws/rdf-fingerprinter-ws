"""UI pages: each asks the API and renders what it answers (design U-3, U-4)."""

from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from http import HTTPStatus
from operator import attrgetter
from typing import Any
from urllib.parse import urlsplit

from flask import (
    Flask,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_wtf.csrf import CSRFError
from werkzeug.wrappers import Response

from fingerprinter.entrypoints.ui import labels
from fingerprinter.entrypoints.ui.api_client import ApiClient
from fingerprinter.entrypoints.ui.api_model import ApiFile, ApiJob
from fingerprinter.entrypoints.ui.exceptions import ApiError
from fingerprinter.entrypoints.ui.forms import FingerprintFileForm, FingerprintSPARQLEndpointForm
from fingerprinter.entrypoints.ui.presenters import (
    JobView,
    diagram_choices,
    downloads,
    present,
)

BYTES_PER_MB = 1024 * 1024
FLASH_ERROR = "error"
FLASH_SUCCESS = "success"
API_EXTENSION = "api"
CONFIG_ACCEPTED_EXTENSIONS = "ACCEPTED_EXTENSIONS"
CONFIG_MAX_UPLOAD_BYTES = "MAX_UPLOAD_BYTES"
REPORT_FILE_NAME = "main.html"
NO_SNIFF = {"X-Content-Type-Options": "nosniff"}
REPORT_HEADERS = NO_SNIFF | {"Content-Security-Policy": "sandbox allow-scripts"}
FRAME_ANCESTORS = "frame-ancestors 'self'"
DIAGRAM_HEADERS = NO_SNIFF | {
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox"
}
REFRESH = {"HX-Refresh": "true"}


def utcnow() -> datetime:
    return datetime.now(UTC)


def _api() -> ApiClient:
    api: ApiClient = current_app.extensions[API_EXTENSION]
    return api


def _upload_limit_mb() -> int:
    limit: int = current_app.config[CONFIG_MAX_UPLOAD_BYTES]
    return max(1, limit // BYTES_PER_MB)


def _sentence(error: ApiError) -> str:
    if error.unreachable:
        return labels.UNREACHABLE
    return labels.problem_sentence(error.problem, upload_limit_mb=_upload_limit_mb())


def _about_job(call: Callable[..., Any], job_id: str, *args: Any) -> Any:
    """A call about one job: an id the API does not accept is a job it does not have."""
    try:
        return call(job_id, *args)
    except ApiError as error:
        if error.status == HTTPStatus.BAD_REQUEST:
            not_found = {"type": f"{labels.PROBLEM_TYPE_PREFIX}JobNotFound"}
            raise ApiError(not_found, HTTPStatus.NOT_FOUND) from error
        raise


def _error_page(error: ApiError) -> tuple[str, int]:
    status = error.status or HTTPStatus.BAD_GATEWAY
    title = labels.NOT_FOUND_TITLE if status == HTTPStatus.NOT_FOUND else labels.FAILED_TITLE
    return render_template("error.html", title=title, message=_sentence(error)), status


def _local_path(target: str | None) -> str:
    """``target`` when it is a path on this site, else the Jobs page (no open redirect).

    A browser drops tabs and line breaks from a URL, so ``/<tab>/host`` would read ``//host``:
    any control character or whitespace refuses the whole target.
    """
    if not target or not all(c.isprintable() and not c.isspace() for c in target):
        return url_for("index")
    parts = urlsplit(target)
    local = target.startswith("/") and not target.startswith(("//", "/\\"))
    return target if local and not (parts.scheme or parts.netloc) else url_for("index")


# --- Jobs -----------------------------------------------------------------------------------------


def _filter() -> labels.Filter:
    show = request.args.get("show")
    return next((f for f in labels.FILTERS if f.id == show), labels.FILTERS[0])


def _all_jobs() -> list[JobView]:
    """Every job, newest first."""
    now = utcnow()
    jobs = (present(job, now) for job in _api().list_jobs())
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
        "paused": "",
        "announce": None,
    }


def index() -> str:
    chosen = _filter()
    try:
        context = _rows_context(chosen, _all_jobs())
    except ApiError as error:
        flash(_sentence(error), FLASH_ERROR)
        context = {"show": chosen.id, "total": None}
    return render_template("jobs/index.html", filters=labels.FILTERS, **context)


def job_rows() -> str:
    """The table body, re-fetched by the page while a job is active (design, live status)."""
    chosen, was = _filter(), request.args.get("was", "")
    try:
        jobs = _all_jobs()
    except ApiError as error:
        # only an API that gave no answer is "paused"; an error answer is said as such
        paused = labels.UPDATES_PAUSED if error.unreachable else labels.SERVER_ERROR
        context = {"show": chosen.id, "rows": [], "polling": True, "was": was, "paused": paused}
        return render_template("jobs/_rows.html", announce="", **context)
    ended = [job for job in jobs if job.id in was.split(",") and not job.active]
    context = _rows_context(chosen, jobs)
    context["announce"] = " ".join(f"{job.source}: {job.label}." for job in ended)
    return render_template("jobs/_rows.html", **context)


# --- The Job page ---------------------------------------------------------------------------------


def _tab_context(job: JobView, tab: labels.JobTab) -> dict[str, Any]:
    """What the chosen tab shows beyond the job itself."""
    if tab == labels.JobTab.DOWNLOADS:
        return {"downloads": downloads(job.files)}
    if tab != labels.JobTab.DIAGRAM:
        return {}
    choices = diagram_choices(job.files.get(labels.FormatId.SVG, ()))
    wanted = request.args.get("diagram")
    shown = next((d for d in choices if d.file == wanted), choices[0] if choices else None)
    if wanted and not (shown and shown.file == wanted):
        flash(labels.UNKNOWN_DIAGRAM, FLASH_ERROR)
    return {"diagrams": choices, "shown": shown}


def job_page(job_id: str) -> str | tuple[str, int]:
    try:
        job = present(_about_job(_api().job, job_id), utcnow())
    except ApiError as error:
        return _error_page(error)
    tab = next((t for t in labels.JobTab if t == request.args.get("tab")), labels.JobTab.REPORT)
    return render_template(
        "jobs/detail.html", job=job, tab=tab, paused="", **_tab_context(job, tab)
    )


def job_state(job_id: str) -> Response | str:
    """The status block, re-fetched by the Job page while the job is active; a final job reloads it."""
    try:
        job = present(_about_job(_api().job, job_id), utcnow())
    except ApiError as error:
        paused = labels.UPDATES_PAUSED if error.unreachable else labels.SERVER_ERROR
        return render_template("jobs/_status.html", job=None, job_id=job_id, paused=paused)
    if not job.active:
        return Response(status=HTTPStatus.OK, headers=REFRESH)
    return render_template("jobs/_status.html", job=job, job_id=job_id, paused="")


# --- New job --------------------------------------------------------------------------------------


def _new_job_page(tab: labels.Tab, form: Any, status: int = HTTPStatus.OK) -> tuple[str, int]:
    config = current_app.config
    page = render_template(
        "jobs/new.html",
        tab=tab,
        form=form,
        accepted=[f".{extension}" for extension in config[CONFIG_ACCEPTED_EXTENSIONS]],
        limit_mb=_upload_limit_mb(),
        formats=labels.FORMATS,
    )
    return page, status


def new_job() -> tuple[str, int]:
    if request.args.get("from") == labels.Tab.FILE:
        return _new_job_page(labels.Tab.FILE, FingerprintFileForm(formdata=None))
    return _new_job_page(labels.Tab.ENDPOINT, FingerprintSPARQLEndpointForm(formdata=None))


def _started(
    form: Any, field: Any, tab: labels.Tab, start: Callable[[], None]
) -> Response | tuple[str, int]:
    """Start the job; on success back to the console, else the form with the sentence at the field."""
    try:
        start()
    except ApiError as error:
        field.errors = [_sentence(error)]
        return _new_job_page(tab, form)
    flash(labels.JOB_STARTED, FLASH_SUCCESS)
    return redirect(url_for("index"))


def start_endpoint_job() -> Response | tuple[str, int]:
    form = FingerprintSPARQLEndpointForm()
    if form.validate_on_submit():
        graphs = (form.graphs.data or "").split()
        start = partial(_api().start_endpoint_job, form.sparql_endpoint_url.data or "", graphs)
        return _started(form, form.sparql_endpoint_url, labels.Tab.ENDPOINT, start)
    return _new_job_page(labels.Tab.ENDPOINT, form)


def start_file_job() -> Response | tuple[str, int]:
    form = FingerprintFileForm()
    if form.validate_on_submit():
        start = partial(_api().start_file_job, form.data_file.data)
        return _started(form, form.data_file, labels.Tab.FILE, start)
    return _new_job_page(labels.Tab.FILE, form)


def upload_too_large(_error: Exception) -> tuple[str, int]:
    """The request was cut off at the UI's own limit, before it reached the API."""
    form = FingerprintFileForm(formdata=None)
    too_large = {"type": f"{labels.PROBLEM_TYPE_PREFIX}UploadTooLarge"}
    form.data_file.errors = [labels.problem_sentence(too_large, upload_limit_mb=_upload_limit_mb())]
    return _new_job_page(labels.Tab.FILE, form, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)


# --- Files and the report -------------------------------------------------------------------------


def _served(file: ApiFile, *, attachment: bool, name: str, headers: dict[str, str]) -> Response:
    """The API's file, as the UI serves it as it arrives: the name and type are the API's."""
    served = Response(file.chunks, mimetype=file.mimetype or "application/octet-stream")
    served.headers.add(
        "Content-Disposition",
        "attachment" if attachment else "inline",
        filename=file.filename or name,
    )
    served.headers.update(headers)
    return served


def job_report(job_id: str) -> Response | tuple[str, int]:
    try:
        file = _about_job(_api().file, job_id, labels.FormatId.HTML)
    except ApiError as error:
        return _error_page(error)
    return _served(file, attachment=False, name=REPORT_FILE_NAME, headers=REPORT_HEADERS)


def job_diagram(job_id: str, name: str) -> Response | tuple[str, int]:
    try:
        file = _about_job(_api().file, job_id, labels.FormatId.SVG, name)
    except ApiError as error:
        return _error_page(error)
    return _served(file, attachment=False, name=name, headers=DIAGRAM_HEADERS)


def job_download(
    job_id: str, report_format: str, name: str | None = None
) -> Response | tuple[str, int]:
    try:
        file = _about_job(_api().file, job_id, report_format, name)
    except ApiError as error:
        return _error_page(error)
    return _served(file, attachment=True, name=name or report_format, headers=NO_SNIFF)


# --- Delete and cancel ----------------------------------------------------------------------------


def _confirmation(job_id: str, dialog: labels.Confirmation, action: str) -> str | tuple[str, int]:
    try:
        job: ApiJob = _about_job(_api().job, job_id)
    except ApiError as error:
        return _error_page(error)
    keep = _local_path(request.args.get("next"))
    return render_template(
        "confirm.html",
        dialog=dialog,
        source=job.source_name,
        action=url_for(action, job_id=job_id, next=keep),
        keep=keep,
    )


def confirm_delete(job_id: str) -> str | tuple[str, int]:
    return _confirmation(job_id, labels.DELETE_CONFIRMATION, "delete_job")


def confirm_cancel(job_id: str) -> str | tuple[str, int]:
    return _confirmation(job_id, labels.CANCEL_CONFIRMATION, "cancel_job")


def _acted(call: Callable[[str], None], job_id: str, done: str, then: str) -> Response:
    try:
        _about_job(call, job_id)
        flash(done, FLASH_SUCCESS)
    except ApiError as error:
        flash(_sentence(error), FLASH_ERROR)
        if error.status == HTTPStatus.NOT_FOUND:  # the page it came from may be that job's own
            then = url_for("index")
    return redirect(then)


def delete_job(job_id: str) -> Response:
    return _acted(_api().delete_job, job_id, labels.REPORT_DELETED, url_for("index"))


def cancel_job(job_id: str) -> Response:
    then = _local_path(request.args.get("next"))
    return _acted(_api().cancel_job, job_id, labels.JOB_CANCELLED, then)


# --- Every response, and an expired form ----------------------------------------------------------


def refuse_framing(response: Response) -> Response:
    """No other site may frame a page of the UI (clickjacking of the confirmations)."""
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    policy = response.headers.get("Content-Security-Policy")
    response.headers["Content-Security-Policy"] = (
        f"{policy}; {FRAME_ANCESTORS}" if policy else FRAME_ANCESTORS
    )
    return response


def _expired_endpoint_form() -> tuple[str, int]:
    form = FingerprintSPARQLEndpointForm(formdata=request.form)  # what was typed is kept
    return _new_job_page(labels.Tab.ENDPOINT, form, HTTPStatus.BAD_REQUEST)


def _expired_file_form() -> tuple[str, int]:
    form = FingerprintFileForm(formdata=None)
    return _new_job_page(labels.Tab.FILE, form, HTTPStatus.BAD_REQUEST)


def form_expired(_error: CSRFError) -> tuple[str, int]:
    """The form that was posted, shown again with a new token and the sentence."""
    flash(labels.FORM_EXPIRED, FLASH_ERROR)
    again: dict[str, Callable[..., str | tuple[str, int]]] = {
        start_endpoint_job.__name__: _expired_endpoint_form,
        start_file_job.__name__: _expired_file_form,
        delete_job.__name__: confirm_delete,
        cancel_job.__name__: confirm_cancel,
    }
    show = again.get(request.endpoint or "")
    if show is None:
        page = render_template("error.html", title=labels.FAILED_TITLE, message=labels.FORM_EXPIRED)
        return page, HTTPStatus.BAD_REQUEST
    body = show(**(request.view_args or {}))
    return body if isinstance(body, tuple) else (body, HTTPStatus.BAD_REQUEST)


ROUTES: tuple[tuple[str, Callable[..., Any], tuple[str, ...]], ...] = (
    ("/", index, ("GET",)),
    ("/jobs/rows", job_rows, ("GET",)),
    ("/jobs/new", new_job, ("GET",)),
    ("/jobs/endpoint", start_endpoint_job, ("POST",)),
    ("/jobs/file", start_file_job, ("POST",)),
    ("/jobs/<job_id>", job_page, ("GET",)),
    ("/jobs/<job_id>/state", job_state, ("GET",)),
    ("/jobs/<job_id>/report", job_report, ("GET",)),
    ("/jobs/<job_id>/diagrams/<name>", job_diagram, ("GET",)),
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
    app.register_error_handler(CSRFError, form_expired)
    app.after_request(refuse_framing)
