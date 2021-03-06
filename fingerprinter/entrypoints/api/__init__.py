#!/usr/bin/python3

# __init__.py
# Date:  14/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Module for configuring and exposing the connexion api server using the Flask framework for API.
"""

import connexion

from fingerprinter.config import RDF_FINGERPRINTER_API_SECRET_KEY

connexion_app = connexion.FlaskApp(__name__, specification_dir='openapi')
connexion_app.add_api('fingerprinter.yml')

app = connexion_app.app
app.config['SECRET_KEY'] = RDF_FINGERPRINTER_API_SECRET_KEY
