# coding=utf-8
"""Fingerprint from UI feature tests."""
from pathlib import Path
from pytest_bdd import (
    given,
    scenarios,
    parsers,
    then,
    when,
)

from fingerprinter import config

CONVERTERS = {
    'file': str
}

scenarios('../features/ui_fingerprinting.feature', example_converters=CONVERTERS)


@when(parsers.parse('I fill in the field {control_id} with {text_value}'))
def i_fill_in_the_field_control_id_with_text_value(scenario_context, browser, control_id, text_value):
    browser.find_element_by_id(control_id).send_keys(scenario_context[text_value])


@when(parsers.parse('I upload in the field {field_id} with {field}'))
@when('I upload in the field <field_id> with <field>')
def i_upload_in_the_field_id_with_file_name(scenario_context, browser, field_id, field):
    file_button = browser.find_element_by_id(field_id)
    file_button.send_keys(str(Path(__file__).parents[1] / scenario_context[field]))


@when(parsers.parse('I navigate to the location {page_location}'))
def i_navigate_to_the_location_page(scenario_context, browser, page_location):
    browser.get(config.RDF_FINGERPRINTER_UI_SERVICE + page_location)


@given(parsers.parse('the {field} with value {value}'))
@given('the <field> with value <value>')
def the_field_with_value(scenario_context, field, value):
    scenario_context[field] = value


@when(parsers.parse('I click on the button with id {control_id}'))
def i_click_on_the_button_with_id_validate_button_id(scenario_context, browser, control_id):
    button = browser.find_element_by_id(control_id)
    button.click()


@then('something happens')
def something_happens():
    """the resulting page contains something_here in the element with id some_id."""
