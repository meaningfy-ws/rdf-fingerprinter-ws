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
from werkzeug.exceptions import BadRequest

from fingerprinter.config import config

INPUT_MIME_TYPES = {
    'rdf': 'application/rdf+xml',
    'trix': 'application/xml',
    'nq': 'application/n-quads',
    'nt': 'application/n-triples',
    'jsonld': 'application/ld+json',
    'n3': 'text/n3',
    'ttl': 'text/turtle',
}

HTML_REPORT_TYPE = 'html'
JSON_REPORT_TYPE = 'html'

REPORT_TYPES = [HTML_REPORT_TYPE, JSON_REPORT_TYPE]
DEFAULT_REPORT_TYPE = REPORT_TYPES[0]

logger = logging.getLogger(config.RDF_FINGERPRINTER_LOGGER)


def _guess_file_type(file: str, accepted_types: dict = None):
    if accepted_types is None:
        accepted_types = INPUT_MIME_TYPES
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
