#!/usr/bin/python3

# api_wrapper.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Service to consume validator API.
"""
import requests

from fingerprinter import config


def fingerprint_sparql_endpoint(sparql_endpoint_url: str, graph: str) -> tuple:
    """
    Method to connect to the fingerprinter api to fingerprint a SPARQL endpoint.
    :param sparql_endpoint_url: The endpoint to fingerprint
    :param graph: a named graph to restrict the fingerprint calculation to
    :return: file, int
    """
    data = {
        'sparql_endpoint_url': sparql_endpoint_url,
    }

    if graph:
        data['graph'] = graph

    response = requests.post(config.RDF_FINGERPRINTER_API_SERVICE + '/validate-sparql-endpoint', data=data)

    return response.content, response.status_code
