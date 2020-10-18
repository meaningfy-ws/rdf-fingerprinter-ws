#!/usr/bin/python3

# test_services_handlers.py
# Date:  17/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from pathlib import Path

from fingerprinter.services.handlers import fingerprint_sparql_endpoint, fingerprint_file, upload_file_to_dataset
from tests.conftest import FakeSPARQLAdapter


def test_upload_file_to_dataset(tmpdir):
    file = tmpdir.join('file.ttl')
    file.write('this is some data')

    adapter = FakeSPARQLAdapter()

    upload_file_to_dataset('dataset', str(file), adapter)

    assert adapter._actions[0] == ('GET', 'dataset')
    assert adapter._actions[1] == ('UPLOAD', 'dataset', str(file))


def test_fingerprint_sparql_endpoint(tmpdir):
    endpoint = ''
    output_location = tmpdir.mkdir('output')

    fingerprint_sparql_endpoint(endpoint, output_location)
    report_path = Path(str(output_location)) / 'fingerprint.html'
    assert report_path.read_text() == 'report'


def test_fingerprint_file(tmpdir):
    file = tmpdir.join('file.ttl')
    output_location = tmpdir.mkdir('output')

    fingerprint_file(file, output_location)
    report_path = Path(str(output_location)) / 'fingerprint.html'
    assert report_path.read_text() == 'report'
