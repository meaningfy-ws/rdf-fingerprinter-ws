# coding=utf-8
"""Fingerprint from UI feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('../features/ui_fingerprinting.feature', 'Fingerprint user provided data')
def test_fingerprint_user_provided_data():
    """Fingerprint user provided data."""


@given('a <fingeprinting_type>')
def a_fingeprinting_type(fingeprinting_type):
    """a <fingeprinting_type>."""
    raise NotImplementedError


@when('the user uploads the <data> and requests the fingerprinting report')
def the_user_uploads_the_data_and_requests_the_fingerprinting_report(data):
    """the user uploads the data and requests the fingerprinting report."""
    raise NotImplementedError


@then('the file is uploaded and sent to the <api_endpoint> for fingerprinting')
def the_file_is_uploaded_and_sent_to_the_api_endpoint_for_fingerprinting(api_endpoint):
    """the file is uploaded and sent to the <api_endpoint> for fingerprinting."""
    raise NotImplementedError


@then('the report is received from the API call')
def the_report_is_received_from_the_api_call():
    """the report is received from the API call."""
    raise NotImplementedError


@then('the user gets the report')
def the_user_gets_the_report():
    """the user gets the report."""
    raise NotImplementedError
