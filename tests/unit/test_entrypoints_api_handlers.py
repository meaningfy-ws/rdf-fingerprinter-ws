#!/usr/bin/python3

# test_entrypoints_api_handlers.py
# Date:  21/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Test connexion/flask api views.
"""
from io import BytesIO
from json import loads, dumps
from unittest.mock import patch, MagicMock

import pytest
from werkzeug.datastructures import FileStorage


@patch('fingerprinter.entrypoints.api.handlers.async_fingerprint_sparql_endpoint.delay')
def test_fingerprint_sparql_endpoint_success(mock_async_fingerprint_sparql_endpoint, api_client, tmpdir):
    task_id = 'task-id'

    mock_async_fingerprint_sparql_endpoint.return_value = MagicMock(id=task_id)

    data = {
        'sparql_endpoint_url': 'http://localhost:3030/dataset/query'
    }

    response = api_client.post('/fingerprint-sparql-endpoint', json=data, content_type='application/json')

    assert response.status_code == 200
    assert task_id in loads(response.data.decode()).get('task_id')


@pytest.mark.parametrize('filename',
                         ['test.rdf', 'test.trix', 'test.nq', 'test.nt', 'test.ttl', 'test.n3', 'test.jsonld'])
@patch('fingerprinter.entrypoints.api.handlers.async_fingerprint_file.delay')
def test_fingerprint_file_success(mock_async_fingerprint_file, filename, api_client, tmpdir):
    task_id = 'task-id'

    mock_async_fingerprint_file.return_value = MagicMock(id=task_id)

    data = {
        'data_file': FileStorage(BytesIO(b'data file content'), filename)
    }

    response = api_client.post('/fingerprint-file', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    assert task_id in loads(response.data.decode()).get('task_id')


def test_fingerprint_file_file_type_exception(api_client):
    unacceptable_filename = 'data.pdf'

    data = {
        'data_file': FileStorage(BytesIO(b'pdf file content'), unacceptable_filename),
    }

    response = api_client.post('/fingerprint-file', data=data, content_type='multipart/form-data')

    assert response.status_code == 415
    assert unacceptable_filename in response.json.get('detail')


@pytest.mark.parametrize("report_type, content_type",
                         [('html', 'text/html'), ('json', 'application/json'),
                          ('zip', 'application/zip')])
@patch('fingerprinter.entrypoints.api.handlers.get_report')
def test_get_fingerprinting_report(mock_get_report, report_type, content_type, api_client, tmpdir):
    uid = 'fingerprinting-report-uid'
    api_endpoint = f'/reports/{uid}?report_type={report_type}'

    report = tmpdir.mkdir('report')
    report = report.join(f'report.{report_type}')
    report.write(report_type)

    mock_get_report.return_value = str(report), f'report.{report_type}'
    response = api_client.get(api_endpoint)

    assert response.status_code == 200
    assert content_type in response.content_type
    assert report_type in response.data.decode()


@patch('fingerprinter.entrypoints.api.handlers.get_report')
def test_get_fingerprinting_report_failure(mock_get_report, api_client, tmpdir):
    uid = 'non-existing-report-uid'
    api_endpoint = f'/reports/{uid}?report_type=html'

    mock_get_report.side_effect = FileNotFoundError
    response = api_client.get(api_endpoint)

    assert response.status_code == 404
    assert 'Fingerprinting doesn\'t exist.' in response.data.decode()


@patch('fingerprinter.entrypoints.api.handlers.get_available_fingerprintings')
def test_get_fingerprintings(mock_get_available_fingerprintings, api_client, tmpdir):
    mock_get_available_fingerprintings.return_value = ['validation1', 'validation2']
    response = api_client.get('/reports')

    assert response.status_code == 200
    assert 'validation1' in response.data.decode()
    assert 'validation2' in response.data.decode()
    assert len(loads(response.data.decode())) == 2


@patch('fingerprinter.entrypoints.api.handlers.delete_report')
def test_delete_report(mock_delete_report, api_client, tmpdir):
    uid = 'fingerprinting-report-uid'
    api_endpoint = f'/reports/{uid}'

    mock_delete_report.return_value = True

    response = api_client.delete(api_endpoint)

    assert response.status_code == 200


@patch('fingerprinter.entrypoints.api.handlers.delete_report')
def test_delete_report_failure(mock_delete_report, api_client, tmpdir):
    uid = 'fingerprinting-report-uid'
    api_endpoint = f'/reports/{uid}'

    mock_delete_report.return_value = False

    response = api_client.delete(api_endpoint)

    assert response.status_code == 404


@patch('fingerprinter.entrypoints.api.handlers.delete_all_reports')
def test_delete_reports(mock_delete_all_reports, api_client, tmpdir):
    api_endpoint = f'/remove-reports'

    mock_delete_all_reports.return_value = True

    response = api_client.delete(api_endpoint)

    assert response.status_code == 200


@patch('fingerprinter.entrypoints.api.handlers.delete_all_reports')
def test_delete_reports_failure(mock_delete_all_reports, api_client, tmpdir):
    api_endpoint = f'/remove-reports'

    mock_delete_all_reports.return_value = False

    response = api_client.delete(api_endpoint)

    assert response.status_code == 404


@patch('fingerprinter.entrypoints.api.handlers.flatten_active_tasks')
@patch('fingerprinter.entrypoints.api.handlers.retrieve_active_tasks')
def test_get_active_tasks(mock_retrieve_active_tasks, mock_flatten_active_tasks, api_client):
    api_endpoint = f'/tasks/active'

    mock_flatten_active_tasks.return_value = [1, 2, 3]

    response = api_client.get(api_endpoint)

    assert response.status_code == 200
    assert '1' in response.data.decode()
    assert '2' in response.data.decode()
    assert '3' in response.data.decode()


@patch('fingerprinter.entrypoints.api.handlers.retrieve_task')
def test_get_task_status(mock_retrieve_task, api_client):
    task_id = 'task-id'
    api_endpoint = f'/tasks/{task_id}'

    mock_retrieve_task.return_value = MagicMock(id=task_id, status='success', result="result")

    response = api_client.get(api_endpoint)

    assert response.status_code == 200
    assert 'success' in response.data.decode()
    assert 'result' in response.data.decode()


@patch('fingerprinter.entrypoints.api.handlers.retrieve_task')
def test_get_task_status_failure(mock_retrieve_task, api_client):
    task_id = 'task-id'
    api_endpoint = f'/tasks/{task_id}'

    mock_retrieve_task.return_value = None

    response = api_client.get(api_endpoint)

    assert response.status_code == 404


@patch('fingerprinter.entrypoints.api.handlers.flatten_active_tasks')
@patch('fingerprinter.entrypoints.api.handlers.retrieve_active_tasks')
@patch('fingerprinter.entrypoints.api.handlers.kill_task')
def test_stop_running_task(mock_kill_task, mock_retrieve_active_tasks, mock_flatten_active_tasks, api_client):
    task_id = 'task-id'
    api_endpoint = f'/tasks/{task_id}'

    mock_flatten_active_tasks.return_value = [{'id': task_id}]

    response = api_client.delete(api_endpoint)

    mock_kill_task.assert_called_once()
    assert response.status_code == 200


@patch('fingerprinter.entrypoints.api.handlers.flatten_active_tasks')
@patch('fingerprinter.entrypoints.api.handlers.retrieve_active_tasks')
@patch('fingerprinter.entrypoints.api.handlers.kill_task')
def test_stop_running_task(mock_kill_task, mock_retrieve_active_tasks, mock_flatten_active_tasks, api_client):
    task_id = 'task-id'
    api_endpoint = f'/tasks/{task_id}'

    mock_flatten_active_tasks.return_value = []

    response = api_client.delete(api_endpoint)

    assert response.status_code == 406
