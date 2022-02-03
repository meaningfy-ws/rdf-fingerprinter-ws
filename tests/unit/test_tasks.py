from unittest.mock import patch

import pytest

from fingerprinter.adapters.celery import async_fingerprint_file, async_fingerprint_sparql_endpoint
from fingerprinter.services.file import dir_exists


@patch('fingerprinter.adapters.celery.build_report_from_file')
def test_async_fingerprint_file(mock_build_report_from_file, api_client, tmpdir,
                                monkeypatch):
    location = tmpdir.mkdir('cleanup')
    data_file = location.join('data-file.ttl')
    data_file.write('some data')

    return_value = async_fingerprint_file(file_path=str(data_file), db_cleanup_location=location, graphs=[])

    mock_build_report_from_file.called_once()
    assert not dir_exists(location)
    assert return_value


@patch('fingerprinter.adapters.celery.build_report_from_sparql_endpoint')
def test_async_fingerprint_sparql_endpoint(mock_build_report_from_sparql_endpoint, api_client, tmpdir):
    location = tmpdir.mkdir('cleanup')
    sparql_endpoint = 'http://example.com/sparql'
    graphs = []

    return_value = async_fingerprint_sparql_endpoint(sparql_endpoint_url=sparql_endpoint, db_cleanup_location=location,
                                                     graphs=graphs)

    mock_build_report_from_sparql_endpoint.called_once()
    assert not dir_exists(location)
    assert return_value
