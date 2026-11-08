"""The UI's HTTP client of the fingerprinter API; each call answers the API's response."""

from urllib.parse import quote

import requests
from werkzeug.datastructures import FileStorage

REQUEST_TIMEOUT_SECONDS = 60


def _segment(value: str) -> str:
    """A value as one URL path segment: no slash, query or fragment can escape it."""
    return quote(value, safe="")


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def fingerprint_sparql_endpoint(self, sparql_endpoint_url: str, graphs: list[str]):
        data: dict[str, str | list[str]] = {"sparql_endpoint_url": sparql_endpoint_url}
        if graphs:
            data["graphs"] = graphs
        return requests.post(
            f"{self.base_url}/fingerprint-sparql-endpoint",
            json=data,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def fingerprint_file(self, data_file: FileStorage):
        files = {"data_file": (data_file.filename, data_file.stream, data_file.mimetype)}
        return requests.post(
            f"{self.base_url}/fingerprint-file", files=files, timeout=REQUEST_TIMEOUT_SECONDS
        )

    def get_reports(self):
        return requests.get(f"{self.base_url}/reports", timeout=REQUEST_TIMEOUT_SECONDS)

    def get_report(self, job_id: str, report_format: str):
        return requests.get(
            f"{self.base_url}/reports/{_segment(job_id)}/{_segment(report_format)}",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def delete_report(self, job_id: str):
        return requests.delete(
            f"{self.base_url}/reports/{_segment(job_id)}", timeout=REQUEST_TIMEOUT_SECONDS
        )

    def get_active_tasks(self):
        return requests.get(f"{self.base_url}/tasks/active", timeout=REQUEST_TIMEOUT_SECONDS)

    def cancel_task(self, task_id: str):
        return requests.delete(
            f"{self.base_url}/tasks/{_segment(task_id)}", timeout=REQUEST_TIMEOUT_SECONDS
        )
