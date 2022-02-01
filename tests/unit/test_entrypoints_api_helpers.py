from werkzeug.exceptions import BadRequest, UnprocessableEntity
import pytest

from fingerprinter.entrypoints.api.helpers import is_url, check_is_url, check_report_extension


def test_is_url():
    url1 = 'https://www.google.com'
    url2 = 'www.google.com'
    url3 = '/some/file/location'
    url4 = 3

    assert is_url(url1)
    assert not is_url(url2)
    assert not is_url(url3)
    assert not is_url(str(url4))


def test_check_is_url():
    url1 = 'https://www.google.com'
    url2 = 'www.google.com'
    url3 = '/some/file/location'

    check_is_url(url1)

    with pytest.raises(BadRequest):
        check_is_url(url2)


@pytest.mark.parametrize('report_type',
                         ['html', 'json', 'zip'])
def test_check_report_extension_success(report_type):
    assert check_report_extension(report_type)


@pytest.mark.parametrize('report_type',
                         ['rdf', 'txt', 'doc'])
def test_check_report_extension_failure(report_type):
    with pytest.raises(UnprocessableEntity):
        assert check_report_extension(report_type)
