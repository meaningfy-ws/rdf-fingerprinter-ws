#!/usr/bin/python3

# views.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
UI pages
"""
import tempfile
from pathlib import Path

from flask import url_for, render_template, flash, send_from_directory
from werkzeug.utils import redirect

from fingerprinter.entrypoints.ui import app
from fingerprinter.entrypoints.ui.api_wrapper import fingerprint_sparql_endpoint as api_fingerprint_sparql_endpoint, \
    fingerprint_file as api_fingerprint_file
from fingerprinter.entrypoints.ui.forms import FingerprintSPARQLEndpointForm, FingerprintFileForm
from fingerprinter.entrypoints.ui.helpers import get_error_message_from_response


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('fingerprint_sparql_endpoint'))


@app.route('/fingerprint-sparql-endpoint', methods=['GET', 'POST'])
def fingerprint_sparql_endpoint():
    form = FingerprintSPARQLEndpointForm()

    if form.validate_on_submit():
        response, status = api_fingerprint_sparql_endpoint(
            sparql_endpoint_url=form.sparql_endpoint_url.data,
            graph=form.graph.data
        )

        if status != 200:
            flash(get_error_message_from_response(response), 'error')
        else:
            with tempfile.TemporaryDirectory() as temp_folder:
                report = Path(temp_folder) / str(f'report.html')
                report.write_bytes(response)
                return send_from_directory(Path(temp_folder), f'report.html', as_attachment=True)

    return render_template('fingerprint/sparql_endpoint_url.html', form=form, title='Fingerprint SPARQL Endpoint')


@app.route('/fingerprint-file', methods=['GET', 'POST'])
def fingerprint_file():
    form = FingerprintFileForm()

    if form.validate_on_submit():
        response, status = api_fingerprint_file(
            data_file=form.data_file.data,
            graph=form.graph.data
        )

        if status != 200:
            flash(get_error_message_from_response(response), 'error')
        else:
            with tempfile.TemporaryDirectory() as temp_folder:
                report = Path(temp_folder) / str(f'report.html')
                report.write_bytes(response)
                return send_from_directory(Path(temp_folder), f'report.html', as_attachment=True)

    return render_template('fingerprint/file.html', form=form, title='Fingerprint File')
