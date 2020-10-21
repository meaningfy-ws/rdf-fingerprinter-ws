#!/usr/bin/python3

# test_services_handlers.py
# Date:  17/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from pathlib import Path
from unittest.mock import patch

from fingerprinter.services.handlers import fingerprint_file, upload_file_to_dataset


def test_upload_file_to_dataset(tmpdir, fake_sparql_adapter):
    file = tmpdir.join('file.ttl')

    with upload_file_to_dataset('dataset', str(file), fake_sparql_adapter):
        pass

    assert fake_sparql_adapter.actions[0] == ('CREATE', 'dataset')
    assert fake_sparql_adapter.actions[1] == ('UPLOAD', ('dataset', str(file)))
    assert fake_sparql_adapter.actions[2] == ('DELETE', 'dataset')


@patch('fingerprinter.services.handlers.generate_endpoint_fingerprint_report')
def test_fingerprint_file(mock_generate_endpoint_fingerprint_report, tmpdir, fake_sparql_adapter):
    output_location = tmpdir.mkdir('output')
    report_path = Path(str(output_location)) / 'fingerprint.html'
    report_path.write_text('report')
    file = tmpdir.join('file.ttl')

    fingerprint_file(file, output_location, fake_sparql_adapter)

    assert fake_sparql_adapter.actions[0][0] == 'CREATE'
    assert fake_sparql_adapter.actions[1][0] == 'UPLOAD'
    assert fake_sparql_adapter.actions[2][0] == 'DELETE'

    assert report_path.read_text() == 'report'
