#!/usr/bin/python3

# test_adapters_helpers.py
# Date:  21/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import pytest

from fingerprinter.adapters.helpers import get_file_format


def test_get_file_format_success_default_file_types():
    file = '/location/file.rdf'
    file_format = get_file_format(file)

    assert file_format == 'application/rdf+xml'


def test_get_file_format_success_custom_file_types():
    file = '/location/file.pdf'
    types = {
        'pdf': 'application/pdf'
    }
    file_format = get_file_format(file, types)

    assert file_format == 'application/pdf'


def test_get_file_format_not_accepted():
    file = '/location/file.docx'
    with pytest.raises(ValueError) as e:
        _ = get_file_format(file)

    assert 'Format of "/location/file.docx" is not supported.' in str(e)
