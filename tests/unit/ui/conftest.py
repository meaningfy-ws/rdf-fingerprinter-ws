import pytest

from tests.unit.ui.fake_api import FakeApi, make_app


@pytest.fixture
def api() -> FakeApi:
    return FakeApi()


@pytest.fixture
def client(api):
    return make_app(api).test_client()
