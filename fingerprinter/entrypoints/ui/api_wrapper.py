#!/usr/bin/python3

# api_wrapper.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Service to consume validator API.
"""
from typing import List

import requests
from werkzeug.datastructures import FileStorage

from fingerprinter import config


def fingerprint_sparql_endpoint(sparql_endpoint_url: str, graphs: List) -> tuple:
    """
    Method to connect to the fingerprinter api to fingerprint a SPARQL endpoint.
    :param sparql_endpoint_url: The endpoint to fingerprint
    :param graphs: a list of named graphs to restrict the fingerprint calculation to
    :return: file, int
    """
    data = {
        'sparql_endpoint_url': sparql_endpoint_url,
    }

    if graphs:
        data['graphs'] = graphs

    response = requests.post(config.RDF_FINGERPRINTER_API_SERVICE + '/fingerprint-sparql-endpoint', json=data)

    return response.content, response.status_code


def fingerprint_file(data_file: FileStorage, graphs: List) -> tuple:
    """
    Method to connect to the fingerprinter api to fingerprint an RDF file.
    :param data_file: the file to be fingerprinted
    :param graphs: a named list of graphs to restrict the fingerprint calculation to
    :return: file, int
    """
    files = {
        'data_file': (data_file.filename, data_file.stream, data_file.mimetype),
    }

    data = dict()
    if graphs:
        data['graphs'] = graphs

    response = requests.post(config.RDF_FINGERPRINTER_API_SERVICE + '/fingerprint-file', data=data, files=files)

    return response.content, response.status_code
