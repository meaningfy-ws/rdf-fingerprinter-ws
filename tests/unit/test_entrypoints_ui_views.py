#!/usr/bin/python3

# test_entrypoints_ui_views.py
# Date:  22/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from io import BytesIO
from json import dumps
from unittest.mock import patch, MagicMock

from bs4 import BeautifulSoup
from werkzeug.datastructures import FileStorage


def _helper_get_request_and_parse(client, url) -> BeautifulSoup:
    response = client.get(url, follow_redirects=True)
    return BeautifulSoup(response.data, 'html.parser')


@patch('fingerprinter.entrypoints.ui.views.api_get_fingerprintings')
def test_index(mock_get_fingerprintings, ui_client):
    ui_url = '/'
    mock_get_fingerprintings.return_value = [[], 200]
    soup = _helper_get_request_and_parse(ui_client, ui_url)

    title = soup.find(id='title')
    assert 'Fingerprinting reports' in title.get_text()


@patch('fingerprinter.entrypoints.ui.views.api_fingerprint_sparql_endpoint')
def test_fingerprint_sparql_endpoint_success(mock_api_fingerprint_sparql_endpoint, ui_client):
    ui_url = '/fingerprint-sparql-endpoint'
    mock_api_fingerprint_sparql_endpoint.return_value = 'ok', 200

    soup = _helper_get_request_and_parse(ui_client, ui_url)

    title = soup.find(id='title')
    assert 'Fingerprint SPARQL Endpoint' in title.get_text()

    data = {
        'sparql_endpoint_url': 'http://endpoint.url',
        'graphs': ''
    }

    response = ui_client.post(ui_url, data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    title = soup.find(id='title')
    assert 'Fingerprint SPARQL Endpoint' in title.get_text()


@patch('fingerprinter.entrypoints.ui.views.api_fingerprint_sparql_endpoint')
def test_fingerprint_sparql_endpoint_failure(mock_api_fingerprint_sparql_endpoint, ui_client):
    ui_url = '/fingerprint-sparql-endpoint'
    exception_content = 'API server error'
    exception_response = {
        'detail': exception_content
    }
    mock_api_fingerprint_sparql_endpoint.return_value = dumps(exception_response), 500

    data = {
        'sparql_endpoint_url': 'http://endpoint.url',
        'graphs': ''
    }

    response = ui_client.post(ui_url, data=data, content_type='multipart/form-data')

    soup = BeautifulSoup(response.data, 'html.parser')
    error_message = soup.find('div', {'class': 'card red lighten-3'})

    assert exception_content in error_message.get_text()


@patch('fingerprinter.entrypoints.ui.views.api_fingerprint_file')
def test_fingerprint_file_success(mock_api_fingerprint_file, ui_client):
    ui_url = '/fingerprint-file'
    mock_api_fingerprint_file.return_value = 'ok', 200

    soup = _helper_get_request_and_parse(ui_client, ui_url)

    title = soup.find(id='title')
    assert 'Fingerprint File' in title.get_text()

    data = {
        'data_file': FileStorage(BytesIO(b'data file content'), 'data.ttl'),
        'graphs': ''
    }

    response = ui_client.post(ui_url, data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    title = soup.find(id='title')
    assert 'Fingerprint File' in title.get_text()


@patch('fingerprinter.entrypoints.ui.views.api_fingerprint_file')
def test_fingerprint_file_failure(mock_api_fingerprint_file, ui_client):
    ui_url = '/fingerprint-file'
    exception_content = 'This file type is not supported'
    exception_response = {
        'detail': exception_content
    }
    mock_api_fingerprint_file.return_value = dumps(exception_response), 415

    data = {
        'data_file': FileStorage(BytesIO(b'data file content'), 'data.ttl'),
        'graphs': ''
    }

    response = ui_client.post(ui_url, data=data, content_type='multipart/form-data')

    soup = BeautifulSoup(response.data, 'html.parser')
    error_message = soup.find('div', {'class': 'card red lighten-3'})

    assert exception_content in error_message.get_text()
