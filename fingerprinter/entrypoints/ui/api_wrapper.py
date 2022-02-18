#!/usr/bin/python3

# api_wrapper.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Service to consume fingerprinter API.
"""
from typing import List

import requests
from werkzeug.datastructures import FileStorage

from fingerprinter.config import config


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

    response = requests.post(f'{config.RDF_FINGERPRINTER_API_SERVICE}/fingerprint-sparql-endpoint', json=data)

    return response.content, response.status_code


def fingerprint_file(data_file: FileStorage) -> tuple:
    """
    Method to connect to the fingerprinter api to fingerprint an RDF file.
    :param data_file: the file to be fingerprinted
    :return: file, int
    """
    files = {
        'data_file': (data_file.filename, data_file.stream, data_file.mimetype),
    }

    response = requests.post(f'{config.RDF_FINGERPRINTER_API_SERVICE}/fingerprint-file', files=files)

    return response.content, response.status_code


def get_fingerprintings() -> tuple:
    """
    Method to connect to the fingerprinter api to get the list of fingerprintings.
    :return: list, int
    """
    response = requests.get(f'{config.RDF_FINGERPRINTER_API_SERVICE}/reports')

    return response.json(), response.status_code


def get_report(fingerprinting_id: str, report_type: str) -> tuple:
    """
    Method to connect to the fingerprinter api to get a report.
    :param fingerprinting_id: the id of the fingerprinting to get the report for
    :param report_type: the type of report to get
    :return: file, int
    """
    response = requests.get(f'{config.RDF_FINGERPRINTER_API_SERVICE}/reports/{fingerprinting_id}',
                            params={'report_type': report_type})

    return response.content, response.status_code


def delete_fingerprinting(fingerprinting_id: str) -> tuple:
    """
    Method to connect to the fingerprinter api to delete a fingerprinting.
    :param fingerprinting_id: the id of the fingerprinting to be deleted
    :return: int
    """
    response = requests.delete(f'{config.RDF_FINGERPRINTER_API_SERVICE}/reports/{fingerprinting_id}')

    return response.json(), response.status_code


def get_active_tasks() -> tuple:
    """
    Method to connect to the fingerprinter api to get the list of active tasks.
    :return: list, int
    """
    response = requests.get(f'{config.RDF_FINGERPRINTER_API_SERVICE}/tasks/active')

    return response.json(), response.status_code


def revoke_task(task_id: str) -> tuple:
    """
    Method to connect to the fingerprinter api to revoke a task.
    :param task_id: the id of the task to be revoked
    :return: int
    """
    response = requests.delete(f'{config.RDF_FINGERPRINTER_API_SERVICE}/tasks/{task_id}')

    return response.content, response.status_code
