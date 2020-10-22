#!/usr/bin/python3

# views.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
UI pages
"""
from flask import url_for, render_template
from werkzeug.utils import redirect

from fingerprinter.entrypoints.ui import app
from fingerprinter.entrypoints.ui.forms import FingerprintSPARQLEndpointForm, FingerprintFileForm


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('fingerprint_sparql_endpoint'))


@app.route('/fingerprint-sparql-endpoint', methods=['GET', 'POST'])
def fingerprint_sparql_endpoint():
    form = FingerprintSPARQLEndpointForm()

    if form.validate_on_submit():
        pass

    return render_template('fingerprint/sparql_endpoint_url.html', form=form, title='Fingerprint SPARQL URL')


@app.route('/fingerprint-file', methods=['GET', 'POST'])
def fingerprint_file():
    form = FingerprintFileForm()

    if form.validate_on_submit():
        pass

    return render_template('fingerprint/file.html', form=form, title='Fingerprint File')
