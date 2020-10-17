#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
OpenAPI method handlers.
"""
import logging

from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)


def fingerprint_file(data_file: FileStorage) -> tuple:
    """
    API method to handle file fingerprinting.
    :param data_file:
    :return:
    """

    return 'ok', 200


def fingerprint_sparql_endpoint(sparql_endpoint_url: str) -> tuple:
    """
    API method to handle SPARQL endpoint fingerprinting.
    :param sparql_endpoint_url:
    :return:
    """

    return 'ok', 200
