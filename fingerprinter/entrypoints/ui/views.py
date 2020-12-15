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

from fingerprinter.config import RDF_FINGERPRINTER_LOGGER
from fingerprinter.entrypoints.ui import app
from fingerprinter.entrypoints.ui.api_wrapper import fingerprint_sparql_endpoint as api_fingerprint_sparql_endpoint, \
    fingerprint_file as api_fingerprint_file
from fingerprinter.entrypoints.ui.forms import FingerprintSPARQLEndpointForm, FingerprintFileForm
from fingerprinter.entrypoints.ui.helpers import get_error_message_from_response

logger = logging.getLogger(RDF_FINGERPRINTER_LOGGER)


@app.route('/', methods=['GET'])
def index():
    logger.debug('request index view')
    return redirect(url_for('fingerprint_sparql_endpoint'))


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
            with tempfile.TemporaryDirectory() as temp_folder:
                report = Path(temp_folder) / str(f'report.html')
                report.write_bytes(response)
                logger.debug('return fingerprint sparql endpoint view')
                return send_from_directory(Path(temp_folder), f'report.html', as_attachment=True)

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
            with tempfile.TemporaryDirectory() as temp_folder:
                report = Path(temp_folder) / str(f'report.html')
                report.write_bytes(response)
                logger.debug('return fingerprint file view')
                return send_from_directory(Path(temp_folder), f'report.html', as_attachment=True)

    logger.debug('return fingerprint file clean view')
    return render_template('fingerprint/file.html', form=form, title='Fingerprint File')
