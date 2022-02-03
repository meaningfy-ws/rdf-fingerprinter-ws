#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Service layer of the fingerprinter web services.
"""
import logging
from contextlib import contextmanager

from fingerprinter.adapters.sparql_adapter import AbstractSPARQLAdapter

logger = logging


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


