#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Service layer of the fingerprinter web services.
"""
import logging
import uuid
from contextlib import contextmanager

from fingerprint.service_layer.handlers import generate_endpoint_fingerprint_report

from fingerprinter import config
from fingerprinter.adapters.sparql_adapter import AbstractSPARQLAdapter
from fingerprinter.config import RDF_FINGERPRINTER_LOGGER

logger = logging.getLogger(RDF_FINGERPRINTER_LOGGER)


@contextmanager
def upload_file_to_dataset(dataset: str, file_path: str, sparql_adapter: AbstractSPARQLAdapter):
    """
        A context manager that creates a dataset, uploads a file into it, and finally deletes the dataset
    :param dataset: dataset name
    :param file_path: location of the file to be uploaded
    :param sparql_adapter: adapter used to perform triplestore operations
    """
    try:
        logger.debug('create dataset')
        sparql_adapter.create_dataset(dataset)
        logger.debug('upload dataset')
        sparql_adapter.upload_file(dataset, file_path)
        yield
    finally:
        logger.debug('delete dataset')
        sparql_adapter.delete_dataset(dataset)


def fingerprint_sparql_endpoint(sparql_endpoint: str, output_location: str, graph: str = '') -> str:
    """
        Fingerprint a SPARQL endpoint using the fingerprinter
        available at https://github.com/meaningfy-ws/rdf-fingerprinter.
    :param sparql_endpoint: SPARQL endpoint for querying the triplestore service
    :param output_location: location for the report to be built in
    :param graph: (optional) restrict the fingerprinting calculation to this graph
    :return: the report location
    """
    logger.debug('start fingerprint sparql endpoint library call')
    report_path = str(generate_endpoint_fingerprint_report(
        sparql_endpoint_url=sparql_endpoint, output_location=output_location,
        external_template_location=config.RDF_FINGERPRINTER_TEMPLATE_LOCATION))

    logger.debug('finish fingerprint sparql endpoint library call')
    return report_path


def fingerprint_file(file_path: str, output_location: str, sparql_adapter: AbstractSPARQLAdapter,
                     graph: str = '') -> str:
    """
        Fingerprint a file using the fingerprinter available at https://github.com/meaningfy-ws/rdf-fingerprinter.
    :param file_path: file to be fingerprinted
    :param output_location: location for the report to be built in
    :param sparql_adapter: adapter used to perform triplestore operations
    :param graph: (optional) restrict the fingerprinting calculation to this graph
    :return:
    """
    logger.debug('start fingerprint file library call')

    dataset_name = str(uuid.uuid4())

    with upload_file_to_dataset(dataset_name, file_path, sparql_adapter):
        sparql_endpoint = f'{config.RDF_FINGERPRINTER_FUSEKI_SERVICE}/{dataset_name}/query'
        report_path = fingerprint_sparql_endpoint(sparql_endpoint, output_location, graph)

    logger.debug('end fingerprint file library call')
    return report_path
