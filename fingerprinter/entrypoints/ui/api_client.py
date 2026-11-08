"""The UI's HTTP client of the fingerprinter API: typed calls that answer values or raise ``ApiError``."""

from collections.abc import Callable, Iterator
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import requests
from werkzeug.datastructures import FileStorage
from werkzeug.http import parse_options_header

from fingerprinter.entrypoints.ui import labels
from fingerprinter.entrypoints.ui.api_model import ApiFile, ApiJob
from fingerprinter.entrypoints.ui.exceptions import ApiError

REQUEST_TIMEOUT_SECONDS = 60
# The library's worst case for a listing is about 65 s: 3 attempts of 20 s a read and 5 s of backoff
# (meaningfy-ws/rdf-fingerprinter#76); the UI waits for it.
LISTING_TIMEOUT_SECONDS = 75
LISTING_TIMED_OUT = {  # the UI's own wait ran out: said as the library's timeout reason is
    "type": f"{labels.PROBLEM_TYPE_PREFIX}GraphListingFailed",
    "detail": "the endpoint did not answer in time",
}
CHUNK_BYTES = 64 * 1024


def _segment(value: str) -> str:
    """A value as one URL path segment: no slash, query or fragment can escape it."""
    return quote(value, safe="")


def _problem(response: requests.Response) -> dict[str, Any] | None:
    try:
        body = response.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def _parsed[T](response: requests.Response, parse: Callable[[Any], T]) -> T:
    """What ``parse`` makes of the JSON body; an answer of another shape is a server error."""
    try:
        return parse(response.json())
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise ApiError(None, HTTPStatus.BAD_GATEWAY) from error


def _chunks(response: requests.Response) -> Iterator[bytes]:
    """The body as it arrives; the connection is closed when the last chunk has been taken."""
    try:
        yield from response.iter_content(CHUNK_BYTES)
    finally:
        response.close()


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _send(
        self, method: str, path: str, *, timeout: int = REQUEST_TIMEOUT_SECONDS, **options: Any
    ) -> requests.Response:
        try:
            response = requests.request(
                method, f"{self.base_url}{path}", timeout=timeout, **options
            )
        except requests.RequestException as error:
            raise ApiError() from error
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            problem = _problem(response)
            response.close()
            raise ApiError(problem, response.status_code)
        return response

    def list_jobs(self) -> list[ApiJob]:
        response = self._send("GET", "/reports")
        return _parsed(response, lambda body: [ApiJob.from_dict(record) for record in body])

    def job(self, job_id: str) -> ApiJob:
        response = self._send("GET", f"/reports/{_segment(job_id)}")
        return _parsed(response, ApiJob.from_dict)

    def endpoint_graphs(self, url: str) -> tuple[str, ...]:
        """The endpoint's named graphs; the API's listing waits for the library's retries."""
        try:
            response = self._send(
                "GET", "/endpoint-graphs", timeout=LISTING_TIMEOUT_SECONDS, params={"url": url}
            )
        except ApiError as error:
            if isinstance(error.__cause__, requests.Timeout):
                raise ApiError(LISTING_TIMED_OUT, HTTPStatus.GATEWAY_TIMEOUT) from error
            raise
        return _parsed(response, lambda body: tuple(str(graph) for graph in body["graphs"]))

    def start_endpoint_job(self, sparql_endpoint_url: str, graphs: list[str]) -> None:
        data: dict[str, str | list[str]] = {"sparql_endpoint_url": sparql_endpoint_url}
        if graphs:
            data["graphs"] = graphs
        self._send("POST", "/fingerprint-sparql-endpoint", json=data)

    def start_file_job(self, data_file: FileStorage) -> None:
        files = {"data_file": (data_file.filename, data_file.stream, data_file.mimetype)}
        self._send("POST", "/fingerprint-file", files=files)

    def file(self, job_id: str, report_format: str, name: str | None = None) -> ApiFile:
        """One format of a job, or (with ``name``) one file the job's record lists under it."""
        path = f"/reports/{_segment(job_id)}/{_segment(report_format)}"
        response = self._send("GET", f"{path}/{_segment(name)}" if name else path, stream=True)
        mimetype, _ = parse_options_header(response.headers.get("Content-Type", ""))
        _, disposition = parse_options_header(response.headers.get("Content-Disposition", ""))
        return ApiFile(_chunks(response), mimetype or None, disposition.get("filename"))

    def delete_job(self, job_id: str) -> None:
        self._send("DELETE", f"/reports/{_segment(job_id)}")

    def cancel_job(self, job_id: str) -> None:
        self._send("DELETE", f"/tasks/{_segment(job_id)}")
