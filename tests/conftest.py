#!/usr/bin/python3

# conftest.py
# Date:  14/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import pytest
from pathlib import Path
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver

from fingerprinter.adapters.sparql_adapter import FusekiSPARQLAdapter, AbstractSPARQLAdapter
from fingerprinter.config import TestingConfig
from fingerprinter.entrypoints.api import app as api_app
from fingerprinter.entrypoints.ui import app as ui_app


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
        self.actions.append(('UPLOAD', (dataset_name, file_path)))


@pytest.fixture(scope='function')
def fake_requests():
    return FakeRequests()


# used for testing the adapter
def helper_sparql_wrapper(triplestore_service_url: str = "http://localhost:3030",
                          http_client=FakeRequests()):
    return FusekiSPARQLAdapter(triplestore_service_url=triplestore_service_url,
                               http_client=http_client)


# used for testing the services where the adapter is used
@pytest.fixture(scope='function')
def fake_sparql_adapter():
    return FakeSPARQLAdapter()


@pytest.fixture
def api_client():
    api_app.config.from_object(TestingConfig())
    return api_app.test_client()


@pytest.fixture
def ui_client():
    ui_app.config.from_object(TestingConfig())
    return ui_app.test_client()


@pytest.fixture(scope="session")
def scenario_context():
    return {}


@pytest.fixture(scope="session")
def browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_driver_args = ["--whitelisted-ips=", "--log-path=chromedriver.log"]
    _browser = WebDriver(chrome_options=chrome_options,
                         service_args=chrome_driver_args)
    _browser.maximize_window()
    yield _browser
    _browser.close()
    _browser.quit()
