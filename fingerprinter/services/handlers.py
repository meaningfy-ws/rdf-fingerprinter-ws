#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Service layer of the fingerprinter web services.
"""
import uuid

import requests
from fingerprint.service_layer.handlers import generate_endpoint_fingerprint_report

from fingerprinter import config
from fingerprinter.adapters.sparql_adapter import AbstractSPARQLAdapter, FusekiSPARQLAdapter


def create_dataset_and_upload_file_to_dataset(dataset: str, file_path: str, sparql_adapter: AbstractSPARQLAdapter):
    sparql_adapter.create_dataset(dataset)
    return sparql_adapter.upload_file(dataset, file_path)


def fingerprint_sparql_endpoint(sparql_endpoint: str, output_location: str, graph: str = '') -> str:
    """
        Fingerprint a SPARQL endpoint using the fingerprinter
        available at https://github.com/meaningfy-ws/rdf-fingerprinter.
    :param sparql_endpoint: SPARQL endpoint for querying the triplestore service
    :param output_location: location for the report to be built in
    :param graph: (optional) restrict the fingerprinting calculation to this graph
    :return: the report location
    """

    return str(generate_endpoint_fingerprint_report(sparql_endpoint, output_location, graph))


def fingerprint_file(file_path: str, output_location: str, graph: str = '') -> str:
    """
        Fingerprint a file using the fingerprinter available at https://github.com/meaningfy-ws/rdf-fingerprinter.
    :param file_path: file to be fingerprinted
    :param output_location: location for the report to be built in
    :param graph: (optional) restrict the fingerprinting calculation to this graph
    :return:
    """
    adapter = FusekiSPARQLAdapter(triplestore_service_url=config.FUSEKI_SERVICE, http_client=requests)
    dataset_name = str(uuid.uuid4())

    create_dataset_and_upload_file_to_dataset(dataset_name, file_path, adapter)

    sparql_endpoint = f'{config.FUSEKI_SERVICE}/{dataset_name}/query'
    report_path = fingerprint_sparql_endpoint(sparql_endpoint, output_location, graph)

    adapter.delete_dataset(dataset_name)

    return report_path
