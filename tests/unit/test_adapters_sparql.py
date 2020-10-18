#!/usr/bin/python3

# test_adapters_sparql.py
# Date:  18/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import pytest

from fingerprinter.adapters.sparql_adapter import FusekiException
from tests.conftest import helper_sparql_wrapper


def test_sparql_wrapper_adapter_upload_file_success(tmpdir, fake_requests):
    fake_requests.status_code = 200
    fake_requests.text = {
        'response': 'success'
    }
    file = tmpdir.join('file.ttl')
    file.write('this is some data')

    sparql_wrapper_adapter = helper_sparql_wrapper(http_client=fake_requests)

    response = sparql_wrapper_adapter.upload_file('dataset', str(file))

    assert response == {'response': 'success'}


def test_sparql_wrapper_adapter_upload_file_failure_fuseki_exception(tmpdir, fake_requests):
    fake_requests.status_code = 500
    fake_requests.text = 'internal error'
    file = tmpdir.join('file.ttl')
    file.write('this is some data')

    sparql_wrapper_adapter = helper_sparql_wrapper(http_client=fake_requests)

    with pytest.raises(FusekiException) as e:
        _ = sparql_wrapper_adapter.upload_file('dataset', str(file))

    assert 'Error connecting to fuseki: internal error' in str(e)
