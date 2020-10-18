#!/usr/bin/python3

# conftest.py
# Date:  14/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import pytest

from fingerprinter.adapters.sparql_adapter import FusekiSPARQLAdapter, AbstractSPARQLAdapter


class FakeRequests:
    def __init__(self):
        self.text = None
        self.status_code = None
        self.url = None

    def get(self, url, **kwargs):
        self.url = url
        return self

    def post(self, url, data=None, json=None, **kwargs):
        self.url = url
        return self

    def json(self):
        return self.text


class FakeSPARQLAdapter(AbstractSPARQLAdapter):
    def __init__(self):
        self.actions = list()

    def create_dataset(self, dataset_name: str):
        self.actions.append(('CREATE', dataset_name))

    def delete_dataset(self, dataset_name: str):
        self.actions.append(('DELETE', dataset_name))

    def get_dataset(self, dataset_name: str) -> dict:
        self.actions.append(('GET', dataset_name))
        return {'name': dataset_name}

    def upload_file(self, dataset_name: str, file_path: str):
        self.actions.append(('UPLOAD', dataset_name, file_path))


@pytest.fixture(scope='function')
def fake_requests():
    return FakeRequests()


def helper_sparql_wrapper(triplestore_service_url: str = "http://localhost:3030cc",
                          http_client=FakeRequests()):
    return FusekiSPARQLAdapter(triplestore_service_url=triplestore_service_url,
                               http_client=http_client)
