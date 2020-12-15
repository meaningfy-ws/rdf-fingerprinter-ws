#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
OpenAPI method handlers.
"""
import logging
import tempfile
from pathlib import Path
from uuid import uuid4

import requests
from flask import send_file
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import UnprocessableEntity, InternalServerError, UnsupportedMediaType
from werkzeug.utils import secure_filename

from fingerprinter import config
from fingerprinter.adapters.sparql_adapter import FusekiSPARQLAdapter
from fingerprinter.config import RDF_FINGERPRINTER_LOGGER
from fingerprinter.entrypoints.api.helpers import REPORT_TYPES, DEFAULT_REPORT_TYPE, _guess_file_type, INPUT_MIME_TYPES
from fingerprinter.services.handlers import fingerprint_sparql_endpoint as service_fingerprint_sparql_endpoint, \
    fingerprint_file as service_fingerprint_file

logger = logging.getLogger(RDF_FINGERPRINTER_LOGGER)


def fingerprint_sparql_endpoint(body: dict, report_type: str = DEFAULT_REPORT_TYPE) -> tuple:
    """
    API method to handle SPARQL endpoint fingerprinting and return report.
    :param body: the json body that comes from the request
        sparql_endpoint_url: SPARQL url to fingerprint
        graphs: a list of named graphs to restrict the fingerprint calculation to
    :param report_type: type of file to be returned. Can be `html`. Defaults to `html`
    :return: the fingerprinting report in the requested format
    :rtype: report file (html), int
    """
    logger.debug('start fingerprinting sparql endpoint')
    if report_type not in REPORT_TYPES:
        exception_text = 'Wrong report_extension format. Accepted formats: ' \
                         f'{", ".join([report_type for report_type in REPORT_TYPES])}'
        logger.exception(exception_text)
        raise UnprocessableEntity(exception_text)  # 422

    try:
        with tempfile.TemporaryDirectory() as temp_folder:
            report_path = service_fingerprint_sparql_endpoint(body['sparql_endpoint_url'], temp_folder,
                                                              body.get('graphs'))
            logger.debug('finish fingerprinting sparql endpoint')
            return send_file(report_path, as_attachment=True, attachment_filename='report.html')  # 200
    except Exception as e:
        logger.exception(str(e))
        raise InternalServerError(str(e))  # 500


def fingerprint_file(body: dict, data_file: FileStorage, report_type: str = DEFAULT_REPORT_TYPE) -> tuple:
    """
    API method to handle file fingerprinting.
    :param body: the json body that comes from the request
        graphs: a list of named graphs to restrict the fingerprint calculation to
    :param data_file: the file to be fingerprinted
    :param report_type: type of file to be returned. Can be `html`. Defaults to `html`:
    :return: the fingerprinting report in the requested format
    :rtype: report file (html), int
    """
    logger.debug('start fingerprinting file')
    if not _guess_file_type(data_file.filename):
        exception_text = f'File type errors: {data_file.filename}. Acceptable types: ' + \
                         ', '.join([f'{key}({value})' for (key, value) in INPUT_MIME_TYPES.items()]) + '.'
        logger.exception(exception_text)
        raise UnsupportedMediaType(exception_text)  # 415

    if report_type not in REPORT_TYPES:
        exception_text = 'Wrong report_extension format. Accepted formats: ' \
                         f'{", ".join([report_type for report_type in REPORT_TYPES])}.'
        logger.exception(exception_text)
        raise UnprocessableEntity(exception_text)  # 422

    try:
        with tempfile.TemporaryDirectory() as temp_folder:
            saved_data_file = Path(temp_folder) / (str(uuid4()) + secure_filename(data_file.filename))
            data_file.save(saved_data_file)

            sparql_adapter = FusekiSPARQLAdapter(config.RDF_FINGERPRINTER_FUSEKI_SERVICE, requests)
            report_path = service_fingerprint_file(str(saved_data_file), temp_folder, sparql_adapter,
                                                   body.get('graphs'))

            logger.debug('finish fingerprinting file')
            return send_file(report_path, as_attachment=True, attachment_filename='report.html')  # 200
    except Exception as e:
        logger.exception(str(e))
        raise InternalServerError(str(e))  # 500
