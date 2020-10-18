#!/usr/bin/python3

# test_services_handlers.py
# Date:  17/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from pathlib import Path

from fingerprinter.services.handlers import fingerprint_sparql_endpoint, fingerprint_file


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
