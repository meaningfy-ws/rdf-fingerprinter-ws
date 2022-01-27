#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
OpenAPI method handlers.
"""
import logging

from flask import send_file
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import UnprocessableEntity, InternalServerError, UnsupportedMediaType

from fingerprinter.adapters.celery import async_fingerprint_sparql_endpoint, async_fingerprint_file
from fingerprinter.entrypoints.api.helpers import REPORT_TYPES, DEFAULT_REPORT_TYPE, _guess_file_type, INPUT_MIME_TYPES, \
    check_is_url
from fingerprinter.services.db import create_db_entry
from fingerprinter.services.file import save_file

# logger = logging.getLogger(config.RDF_FINGERPRINTER_LOGGER)
logger = logging


def fingerprint_sparql_endpoint(body: dict) -> tuple:
    """
    API method to handle SPARQL endpoint fingerprinting and return report.
    :param body: the json body that comes from the request
        sparql_endpoint_url: SPARQL url to fingerprint
        graphs: a list of named graphs to restrict the fingerprint calculation to
    :return:
    :rtype:
    """
    logger.debug('start fingerprinting sparql endpoint')
    sparql_endpoint_url = body.get('sparql_endpoint_url')
    check_is_url(sparql_endpoint_url)

    graphs = body.get('graphs', [])

    db_location = create_db_entry()
    task = async_fingerprint_sparql_endpoint.delay(sparql_endpoint_url=sparql_endpoint_url,
                                                   db_cleanup_location=db_location, graphs=graphs)

    logger.debug(f'task executed with id: {task.id}')
    return {'task_id': task.id}, 200


def fingerprint_file(body: dict, data_file: FileStorage) -> tuple:
    """
    API method to handle file fingerprinting.
    :param body: the json body that comes from the request
        graphs: a list of named graphs to restrict the fingerprint calculation to
    :param data_file: the file to be fingerprinted
    :return: the fingerprinting report in the requested format
    :rtype: report file (html), int
    """
    logger.debug('start fingerprinting file')

    if not _guess_file_type(data_file.filename):
        exception_text = f'File type errors: {data_file.filename}. Acceptable types: ' + \
                         ', '.join([f'{key}({value})' for (key, value) in INPUT_MIME_TYPES.items()]) + '.'
        logger.exception(exception_text)
        raise UnsupportedMediaType(exception_text)  # 415

    db_location = create_db_entry()
    file_to_fingerprint = save_file(data_file, db_location)

    graphs = body.get('graphs', [])
    task = async_fingerprint_file.delay(file_path=file_to_fingerprint, db_cleanup_location=db_location, graphs=graphs)

    logger.debug(f'task executed with id: {task.id}')
    return {'task_id': task.id}, 200


def get_fingerprinting_report(report_path: str, report_type: str = DEFAULT_REPORT_TYPE) -> tuple:
    """
    API method to return a fingerprinting report.
    :param report_path: the path to the report file
    :param report_type: type of file to be returned. Can be `html`. Defaults to `html`
    :return: the fingerprinting report in the requested format
    :rtype: report file (html), int
    """
    if report_type not in REPORT_TYPES:
        exception_text = 'Wrong report_extension format. Accepted formats: ' \
                         f'{", ".join([report_type for report_type in REPORT_TYPES])}.'
        logger.exception(exception_text)
        raise UnprocessableEntity(exception_text)  # 422

    try:
        return send_file(report_path, as_attachment=True, attachment_filename='report.html')  # 200
    except Exception as e:
        logger.exception(str(e))
        raise InternalServerError(str(e))  # 500
