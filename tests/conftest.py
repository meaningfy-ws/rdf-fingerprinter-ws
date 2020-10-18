#!/usr/bin/python3

# conftest.py
# Date:  14/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import pytest

from fingerprinter.adapters.sparql_adapter import SPARQLWrapperAdapter


class FakeRequests:
    def __init__(self):
        self.text = None
        self.status_code = None
        self.url = None

    def post(self, url, data=None, json=None, **kwargs):
        self.url = url
        return self

    def json(self):
        return self.text


@pytest.fixture(scope='function')
def fake_requests():
    return FakeRequests()


def helper_sparql_wrapper(triplestore_service_url: str = "http://localhost:3030cc",
                          http_client=FakeRequests()):
    return SPARQLWrapperAdapter(triplestore_service_url=triplestore_service_url,
                                http_client=http_client)
