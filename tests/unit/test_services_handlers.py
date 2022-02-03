#!/usr/bin/python3

# test_services_handlers.py
# Date:  17/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from pathlib import Path
from unittest.mock import patch

from fingerprinter.services.handlers import upload_file_to_dataset


def test_upload_file_to_dataset(tmpdir, fake_sparql_adapter):
    file = tmpdir.join('file.ttl')

    with upload_file_to_dataset('dataset', str(file), fake_sparql_adapter):
        pass

    assert fake_sparql_adapter.actions[0] == ('CREATE', 'dataset')
    assert fake_sparql_adapter.actions[1] == ('UPLOAD', ('dataset', str(file)))
    assert fake_sparql_adapter.actions[2] == ('DELETE', 'dataset')
