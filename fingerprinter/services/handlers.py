#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Service layer of the fingerprinter web services.
"""
from pathlib import Path

from fingerprinter.adapters.sparql_adapter import AbstractSPARQLAdapter


def upload_file_to_dataset(dataset: str, file_path: str, sparql_adapter: AbstractSPARQLAdapter):
    sparql_adapter.get_dataset(dataset)
    return sparql_adapter.upload_file(dataset, file_path)


def fingerprint_sparql_endpoint(sparql_endpoint: str, output_location: str, graph: str = ''):
    """

    :param sparql_endpoint:
    :param output_location:
    :param graph:
    :return:
    """
    # generate_endpoint_fingerprint_report(sparql_endpoint, output_location, graph)
    report_path = Path(output_location) / 'fingerprint.html'
    report_path.write_text('report')


def fingerprint_file(file, output_location: str, graph: str = None):
    """

    :param file:
    :param output_location:
    :param graph:
    :return:
    """
    # do something with file
    sparql_endpoint = ''
    fingerprint_sparql_endpoint(sparql_endpoint, output_location, graph)
