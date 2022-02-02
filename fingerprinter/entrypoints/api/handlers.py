#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
OpenAPI method handlers.
"""
import logging
from json import dumps

from flask import send_file
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import UnsupportedMediaType, NotFound, NotAcceptable

from fingerprinter.adapters.celery import async_fingerprint_sparql_endpoint, async_fingerprint_file
from fingerprinter.config import config
from fingerprinter.entrypoints.api.helpers import _guess_file_type, check_is_url, check_report_extension
from fingerprinter.services.db import create_db_entry
from fingerprinter.services.file import save_file
from fingerprinter.services.report_handling import get_available_fingerprintings, get_report, delete_report, \
    delete_all_reports
from fingerprinter.services.tasks import retrieve_task, flatten_active_tasks, retrieve_active_tasks, kill_task

logger = logging.getLogger(config.RDF_FINGERPRINTER_LOGGER)


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
                         ', '.join([f'{key}({value})' for (key, value) in config.INPUT_MIME_TYPES.items()]) + '.'
        logger.exception(exception_text)
        raise UnsupportedMediaType(exception_text)  # 415

    db_location = create_db_entry()
    file_to_fingerprint = save_file(data_file, db_location)

    graphs = body.get('graphs', [])
    task = async_fingerprint_file.delay(file_path=file_to_fingerprint, db_cleanup_location=db_location, graphs=graphs)

    logger.debug(f'task executed with id: {task.id}')
    return {'task_id': task.id}, 200


def get_fingerprintings() -> tuple:
    """
    API method to return all fingerprinting reports.
    :return: all fingerprinting reports
    :rtype: list of fingerprinting reports meta
    """
    fingerprintings = get_available_fingerprintings(config.RDF_FINGERPRINTER_REPORTS_DB)
    return fingerprintings, 200


def get_fingerprinting_report(uid: str, report_type: str = config.DEFAULT_REPORT_TYPE) -> tuple:
    """
    API method to return a fingerprinting report.
    :param uid: the uid of the fingerprinting report
    :param report_type: type of file to be returned. Can be `html` or `json`. Defaults to `html`
    :return: the fingerprinting report in the requested format
    :rtype: report file, int
    """
    check_report_extension(report_type)
    logger.exception(f'get fingerprinting report: {uid}')
    try:
        location, filename = get_report(uid=uid, extension=report_type,
                                        reports_location=config.RDF_FINGERPRINTER_REPORTS_DB)
        return send_file(location, attachment_filename=filename)
    except FileNotFoundError:
        raise NotFound('Fingerprinting doesn\'t exist.')


def delete_fingerprinting(uid: str) -> tuple:
    """
    API method to delete a fingerprinting report.
    :param uid: the uid of the fingerprinting report
    """
    removed = delete_report(uid=uid, reports_location=config.RDF_FINGERPRINTER_REPORTS_DB)
    if removed:
        return {'message': f'Fingerprinting with {uid} successfully removed'}, 200
    else:
        raise NotFound(f'Fingerprinting with uid {uid} doesn\'t exist.')


def delete_all_fingerprintings() -> tuple:
    """
    API method to delete all fingerprinting reports.
    """
    removed = delete_all_reports(reports_location=config.RDF_FINGERPRINTER_REPORTS_DB)
    if removed:
        return {'message': 'All fingerprintings successfully removed'}, 200
    else:
        raise NotFound('No fingerprintings found.')


def get_active_tasks() -> tuple:
    """
    Get all active celery tasks
    :return: dict of celery workers and their active tasks
    """
    try:
        tasks = flatten_active_tasks(retrieve_active_tasks())
    except AttributeError:
        return [], 200
    return tasks, 200


def get_task_status(task_id: str) -> tuple:
    """
    Get specified task status data
    :param task_id: Id of task to get status for
    :return: dict
    """
    task = retrieve_task(task_id)
    if task:
        try:
            result = dumps(task.result)
        except TypeError:
            result = ''

        data = {
            'task_id': task.id,
            'status': task.status,
            'result': result
        }
        return data, 200

    raise NotFound(f'Task with {task_id} doesn\'t exist')  # 404


def stop_running_task(task_id: str) -> tuple:
    """
    Revoke a task
    :param task_id: Id of task to revoke
    """
    try:
        tasks = flatten_active_tasks(retrieve_active_tasks())
        task = next(task for task in tasks if task["id"] == task_id)
        kill_task(task, config.RDF_FINGERPRINTER_REPORTS_DB)
    except:
        raise NotAcceptable('task already finished executing or does not exist')  # 406

    return {'message': f'task {task_id} set for revoking.'}, 200
