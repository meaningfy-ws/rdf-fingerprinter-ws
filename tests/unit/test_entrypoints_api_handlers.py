#!/usr/bin/python3

# test_entrypoints_api_handlers.py
# Date:  21/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Test connexion/flask api views.
"""
from io import BytesIO
from unittest.mock import patch

import pytest
from werkzeug.datastructures import FileStorage


@patch('fingerprinter.entrypoints.api.handlers.service_fingerprint_sparql_endpoint')
def test_fingerprint_sparql_endpoint_success(mock_service_fingerprint_sparql_endpoint, api_client, tmpdir):
    report_path = tmpdir.join('report.html')
    report_path.write('fingerprinting success')
    mock_service_fingerprint_sparql_endpoint.return_value = report_path

    data = {
        'sparql_endpoint_url': 'http://localhost:3030/dataset/query'
    }

    response = api_client.post('/fingerprint-sparql-endpoint', json=data, content_type='application/json')

    assert response.status_code == 200
    assert 'text/html' in response.content_type
    assert 'fingerprinting success' in response.data.decode()


def test_fingerprint_sparql_endpoint_report_type_not_accepted(api_client):
    data = {
        'sparql_endpoint_url': 'http://localhost:3030/dataset/query'
    }
    api_endpoint = '/fingerprint-sparql-endpoint?report_type={report_type}'
    report_type = 'pdf'

    response = api_client.post(api_endpoint.format(report_type=report_type), json=data,
                               content_type='application/json')

    assert response.status_code == 422
    assert 'Wrong report_extension format. Accepted formats: html' in response.json.get('detail')


@pytest.mark.parametrize('filename',
                         ['test.rdf', 'test.trix', 'test.nq', 'test.nt', 'test.ttl', 'test.n3', 'test.jsonld'])
@patch('fingerprinter.entrypoints.api.handlers.service_fingerprint_file')
def test_fingerprint_file_success(mock_service_fingerprint_file, filename, api_client, tmpdir):
    report_path = tmpdir.join('report.html')
    report_path.write('fingerprinting success')
    mock_service_fingerprint_file.return_value = report_path

    data = {
        'data_file': FileStorage(BytesIO(b'data file content'), filename)
    }

    response = api_client.post('/fingerprint-file', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    assert 'text/html' in response.content_type
    assert 'fingerprinting success' in response.data.decode()


def test_fingerprint_file_file_type_exception(api_client):
    unacceptable_filename = 'data.pdf'

    data = {
        'data_file': FileStorage(BytesIO(b'pdf file content'), unacceptable_filename),
    }

    response = api_client.post('/fingerprint-file', data=data, content_type='multipart/form-data')

    assert response.status_code == 415
    assert unacceptable_filename in response.json.get('detail')


def test_fingerprint_file_report_type_not_accepted(api_client, tmpdir):
    data = {
        'data_file': FileStorage(BytesIO(b'data file content'), 'file.ttl')
    }
    api_endpoint = '/fingerprint-file?report_type={report_type}'
    report_type = 'pdf'

    response = api_client.post(api_endpoint.format(report_type=report_type), data=data,
                               content_type='multipart/form-data')

    assert response.status_code == 422
    assert 'Wrong report_extension format. Accepted formats: html' in response.json.get('detail')
