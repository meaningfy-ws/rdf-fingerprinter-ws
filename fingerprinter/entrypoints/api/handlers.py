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


def fingerprint_file(body: dict, data_file: FileStorage, report_extension: str = 'html') -> tuple:
    """
    API method to handle file fingerprinting.
    :param body:
        graph:
    :param data_file:
    :return:
    """

    return 'ok', 200


def fingerprint_sparql_endpoint(body: dict, report_extension: str = 'html') -> tuple:
    """
    API method to handle SPARQL endpoint fingerprinting.
    :param body:
        sparql_endpoint_url:
        graph:
    :return:
    """

    return 'ok', 200
