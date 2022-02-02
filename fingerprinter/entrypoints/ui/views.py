#!/usr/bin/python3

# views.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
UI pages
"""
import logging
import tempfile
from pathlib import Path

from flask import url_for, render_template, flash, send_from_directory
from werkzeug.utils import redirect

from fingerprinter.config import config
from fingerprinter.entrypoints.ui import app
from fingerprinter.entrypoints.ui.api_wrapper import get_report, \
    fingerprint_sparql_endpoint as api_fingerprint_sparql_endpoint, \
    fingerprint_file as api_fingerprint_file, \
    get_fingerprintings as api_get_fingerprintings, \
    delete_fingerprinting as api_delete_fingerprinting, \
    get_active_tasks as api_get_active_tasks, \
    revoke_task as api_revoke_task
from fingerprinter.entrypoints.ui.forms import FingerprintSPARQLEndpointForm, FingerprintFileForm
from fingerprinter.entrypoints.ui.helpers import get_error_message_from_response

logger = logging.getLogger(config.RDF_FINGERPRINTER_LOGGER)


@app.route('/', methods=['GET'])
def index():
    logger.debug('request index view')
    fingerprintings, _ = api_get_fingerprintings()
    print(fingerprintings)

    return render_template('index.html', fingerprintings=fingerprintings)


@app.route('/fingerprint-sparql-endpoint', methods=['GET', 'POST'])
def fingerprint_sparql_endpoint():
    logger.debug('request fingerprint sparql endpoint view')

    form = FingerprintSPARQLEndpointForm()

    if form.validate_on_submit():
        response, status = api_fingerprint_sparql_endpoint(
            sparql_endpoint_url=form.sparql_endpoint_url.data,
            graphs=form.graphs.data.split()
        )

        if status != 200:
            exception_text = get_error_message_from_response(response)
            logger.exception(exception_text)
            flash(exception_text, 'error')
        else:
            flash('fingerprinting successfully started', 'success')
            logger.debug('render active tasks view')
            # return redirect(url_for('get_active_tasks'))

    logger.debug('return fingerprint sparql endpoint clean view')
    return render_template('fingerprint/sparql_endpoint_url.html', form=form, title='Fingerprint SPARQL Endpoint')


@app.route('/fingerprint-file', methods=['GET', 'POST'])
def fingerprint_file():
    logger.debug('request fingerprint file clean view')

    form = FingerprintFileForm()

    if form.validate_on_submit():
        response, status = api_fingerprint_file(
            data_file=form.data_file.data,
            graphs=form.graphs.data.split()
        )

        if status != 200:
            exception_text = get_error_message_from_response(response)
            logger.exception(exception_text)
            flash(exception_text, 'error')
        else:
            flash('fingerprinting successfully started', 'success')
            logger.debug('render active tasks view')
            # return redirect(url_for('get_active_tasks'))

    logger.debug('return fingerprint file clean view')
    return render_template('fingerprint/file.html', form=form, title='Fingerprint File')


@app.route('/fingerprintings/<fingerprinting_id>/<report_type>', methods=['GET'])
def download_report(fingerprinting_id: str, report_type: str):
    logger.debug(
        f'request fingerprinting report download view for fingerprinting id {fingerprinting_id}, report type: {report_type}')
    try:
        with tempfile.TemporaryDirectory() as temp_folder:
            report_content, _ = get_report(fingerprinting_id=fingerprinting_id, report_type=report_type)
            file_name = f'{fingerprinting_id}_{report_type}.{report_type}'
            report = Path(temp_folder) / file_name
            report.write_bytes(report_content)
            logger.debug(f'report file {report} successfully written')
            return send_from_directory(Path(temp_folder), file_name, as_attachment=True)
    except Exception as e:
        logger.exception(str(e))
        flash(str(e), 'error')
        return redirect(url_for('index'))


@app.route('/reports/<fingerprinting_id>')
def delete_fingerprinting(fingerprinting_id: str):
    logger.debug(f'request fingerprinting report delete view for fingerprinting id {fingerprinting_id}')
    response, status = api_delete_fingerprinting(fingerprinting_id=fingerprinting_id)

    if status != 200:
        exception_text = get_error_message_from_response(response)
        logger.exception(exception_text)
        flash(exception_text, 'error')
    else:
        flash('fingerprinting successfully deleted', 'success')

    return redirect(url_for('index'))


@app.route('/tasks')
def get_active_tasks():
    logger.debug('request active tasks view')
    active_tasks, _ = api_get_active_tasks()
    logger.debug('render active tasks view')
    return render_template('tasks/view_active_tasks.html', tasks=active_tasks)


@app.route('/revoke-task/<task_id>')
def revoke_task(task_id: str):
    logger.debug(f'request revoke task view for task id {task_id}')
    response, status = api_revoke_task(task_id=task_id)

    if status == 200:
        flash(response, 'success')
    else:
        logger.exception(response)
        flash(response, 'error')

    return redirect(url_for('get_active_tasks'))
