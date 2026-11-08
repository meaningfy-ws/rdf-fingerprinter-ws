#!/usr/bin/python3

# test_entrypoints_ui_views.py
# Date:  22/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from io import BytesIO
from json import dumps
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from werkzeug.datastructures import FileStorage


def _helper_get_request_and_parse(client, url) -> BeautifulSoup:
    response = client.get(url, follow_redirects=True)
    return BeautifulSoup(response.data, "html.parser")


@patch("fingerprinter.entrypoints.ui.views.api_get_fingerprintings")
def test_index(mock_get_fingerprintings, ui_client):
    ui_url = "/"
    mock_get_fingerprintings.return_value = [[], 200]
    soup = _helper_get_request_and_parse(ui_client, ui_url)

    title = soup.find(id="title")
    assert "Fingerprinting reports" in title.get_text()


@patch("fingerprinter.entrypoints.ui.views.api_get_active_tasks")
@patch("fingerprinter.entrypoints.ui.views.api_fingerprint_sparql_endpoint")
def test_fingerprint_sparql_endpoint_success(
    mock_api_fingerprint_sparql_endpoint, mock_api_get_active_tasks, ui_client
):
    ui_url = "/fingerprint-sparql-endpoint"
    mock_api_fingerprint_sparql_endpoint.return_value = "ok", 200
    mock_api_get_active_tasks.return_value = [], 200

    soup = _helper_get_request_and_parse(ui_client, ui_url)

    title = soup.find(id="title")
    assert "Fingerprint SPARQL Endpoint" in title.get_text()

    data = {"sparql_endpoint_url": "http://endpoint.url", "graphs": ""}

    response = ui_client.post(
        ui_url, data=data, content_type="multipart/form-data", follow_redirects=True
    )

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    title = soup.find(id="title")
    assert "List of active tasks" in title.get_text()


@patch("fingerprinter.entrypoints.ui.views.api_fingerprint_sparql_endpoint")
def test_fingerprint_sparql_endpoint_failure(mock_api_fingerprint_sparql_endpoint, ui_client):
    ui_url = "/fingerprint-sparql-endpoint"
    exception_content = "API server error"
    exception_response = {"detail": exception_content}
    mock_api_fingerprint_sparql_endpoint.return_value = dumps(exception_response), 500

    data = {"sparql_endpoint_url": "http://endpoint.url", "graphs": ""}

    response = ui_client.post(ui_url, data=data, content_type="multipart/form-data")

    soup = BeautifulSoup(response.data, "html.parser")
    error_message = soup.find("div", {"class": "card red lighten-3"})

    assert exception_content in error_message.get_text()


@patch("fingerprinter.entrypoints.ui.views.api_get_active_tasks")
@patch("fingerprinter.entrypoints.ui.views.api_fingerprint_file")
def test_fingerprint_file_success(mock_api_fingerprint_file, mock_api_get_active_tasks, ui_client):
    ui_url = "/fingerprint-file"
    mock_api_fingerprint_file.return_value = "ok", 200
    mock_api_get_active_tasks.return_value = [], 200

    soup = _helper_get_request_and_parse(ui_client, ui_url)

    title = soup.find(id="title")
    assert "Fingerprint File" in title.get_text()

    data = {"data_file": FileStorage(BytesIO(b"data file content"), "data.ttl")}

    response = ui_client.post(
        ui_url, data=data, content_type="multipart/form-data", follow_redirects=True
    )

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    title = soup.find(id="title")
    assert "List of active tasks" in title.get_text()


@patch("fingerprinter.entrypoints.ui.views.api_fingerprint_file")
def test_fingerprint_file_failure(mock_api_fingerprint_file, ui_client):
    ui_url = "/fingerprint-file"
    exception_content = "This file type is not supported"
    exception_response = {"detail": exception_content}
    mock_api_fingerprint_file.return_value = dumps(exception_response), 415

    data = {"data_file": FileStorage(BytesIO(b"data file content"), "data.ttl"), "graphs": ""}

    response = ui_client.post(ui_url, data=data, content_type="multipart/form-data")

    soup = BeautifulSoup(response.data, "html.parser")
    error_message = soup.find("div", {"class": "card red lighten-3"})

    assert exception_content in error_message.get_text()


@patch("fingerprinter.entrypoints.ui.views.get_report")
def test_download_report_sends_the_api_file(mock_get_report, ui_client):
    mock_get_report.return_value = b"<html>report</html>", 200

    response = ui_client.get("/fingerprintings/uid-1/html")

    mock_get_report.assert_called_once_with(fingerprinting_id="uid-1", report_type="html")
    assert response.status_code == 200
    assert response.data == b"<html>report</html>"
    assert "uid-1_html.html" in response.headers["Content-Disposition"]


@patch("fingerprinter.entrypoints.ui.views.api_get_fingerprintings")
@patch("fingerprinter.entrypoints.ui.views.get_report")
def test_download_report_failure_returns_to_the_list(
    mock_get_report, mock_get_fingerprintings, ui_client
):
    mock_get_report.side_effect = ConnectionError("API unreachable")
    mock_get_fingerprintings.return_value = [[], 200]

    soup = _helper_get_request_and_parse(ui_client, "/fingerprintings/uid-1/html")

    assert "API unreachable" in soup.find("div", {"class": "card red lighten-3"}).get_text()


@patch("fingerprinter.entrypoints.ui.views.api_get_fingerprintings")
@patch("fingerprinter.entrypoints.ui.views.api_delete_fingerprinting")
def test_delete_fingerprinting_success(mock_delete, mock_get_fingerprintings, ui_client):
    mock_delete.return_value = {"message": "removed"}, 200
    mock_get_fingerprintings.return_value = [[], 200]

    soup = _helper_get_request_and_parse(ui_client, "/reports/uid-1")

    mock_delete.assert_called_once_with(fingerprinting_id="uid-1")
    assert "successfully deleted" in soup.find("div", {"class": "card blue lighten-3"}).get_text()


@patch("fingerprinter.entrypoints.ui.views.api_get_fingerprintings")
@patch("fingerprinter.entrypoints.ui.views.api_delete_fingerprinting")
def test_delete_fingerprinting_failure(mock_delete, mock_get_fingerprintings, ui_client):
    mock_delete.return_value = (
        dumps({"status": 404, "title": "Not Found", "detail": "no such report"}),
        404,
    )
    mock_get_fingerprintings.return_value = [[], 200]

    soup = _helper_get_request_and_parse(ui_client, "/reports/uid-1")

    assert "no such report" in soup.find("div", {"class": "card red lighten-3"}).get_text()


@patch("fingerprinter.entrypoints.ui.views.api_get_active_tasks")
def test_active_tasks_are_listed(mock_get_active_tasks, ui_client):
    mock_get_active_tasks.return_value = (
        [{"id": "task-1", "type": "fingerprint_file", "kwargs": {}}],
        200,
    )

    soup = _helper_get_request_and_parse(ui_client, "/tasks")

    assert soup.find(id="stop-task-task-1")


@pytest.mark.parametrize(
    ("status", "card"), [(200, "card blue lighten-3"), (406, "card red lighten-3")]
)
@patch("fingerprinter.entrypoints.ui.views.api_get_active_tasks")
@patch("fingerprinter.entrypoints.ui.views.api_revoke_task")
def test_revoke_task_shows_the_outcome(mock_revoke, mock_get_active_tasks, status, card, ui_client):
    mock_revoke.return_value = "task task-1 set for revoking.", status
    mock_get_active_tasks.return_value = [], 200

    soup = _helper_get_request_and_parse(ui_client, "/revoke-task/task-1")

    mock_revoke.assert_called_once_with(task_id="task-1")
    assert "task task-1 set for revoking." in soup.find("div", {"class": card}).get_text()
