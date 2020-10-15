#!/usr/bin/python3

# views.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
UI pages
"""

from fingerprinter.entrypoints.ui import app


@app.route('/', methods=['GET'])
def index():
    return '<h1>Hello</h1>', 200


@app.route('/fingerprint-file', methods=['GET', 'POST'])
def fingerprint_file():
    return '<h1>File</h1>', 200


@app.route('/fingerprint-sparql-endpoint', methods=['GET', 'POST'])
def fingerprint_sparql_endpoint():
    return '<h1>Endpoint</h1>', 200
