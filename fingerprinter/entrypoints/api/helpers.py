#!/usr/bin/python3

# helpers.py
# Date:  21/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
API helper methods or constants
"""
import logging
from urllib.parse import urlparse

from rdflib.util import guess_format
from werkzeug.exceptions import BadRequest, UnprocessableEntity

from fingerprinter.config import config

logger = logging.getLogger(config.RDF_FINGERPRINTER_LOGGER)


def _guess_file_type(file: str, accepted_types: dict = None):
    if accepted_types is None:
        accepted_types = config.INPUT_MIME_TYPES
    return guess_format(str(file), accepted_types)


def is_url(url: str) -> bool:
    """
    Check if a string is a valid URL
    :param url: the string to check
    :return: True if the string is a valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def check_is_url(url: str):
    """
    Check if url is valid
    :param url: url to check if is valid
    """
    if not is_url(url):
        exception_text = 'Wrong url format. Example: http://example.com'
        logger.exception(exception_text)
        raise BadRequest(exception_text)  # 400
    return True


def check_report_extension(report_type: str) -> bool:
    """
    Check if requested report is accepted.
    :param report_type: the name of the report
    :return: the extension of the report
    :rtype: str
    """
    if report_type not in config.REPORT_TYPES:
        exception_text = 'Wrong report_type format. Accepted formats: ' \
                         f'{", ".join([report_type for report_type in config.REPORT_TYPES])}.'
        logger.exception(exception_text)
        raise UnprocessableEntity(exception_text)  # 422

    return True
