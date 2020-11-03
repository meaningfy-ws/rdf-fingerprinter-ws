#!/usr/bin/python3

# config.py
# Date:  14/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Project wide configuration file.
"""

import os

RDF_FINGERPRINTER_DEBUG = os.environ.get('RDF_FINGERPRINTER_DEBUG')

RDF_FINGERPRINTER_FUSEKI_PORT = os.environ.get('RDF_FINGERPRINTER_FUSEKI_PORT', 3020)
RDF_FINGERPRINTER_FUSEKI_LOCATION = os.environ.get('RDF_FINGERPRINTER_FUSEKI_LOCATION', 'http://fuseki')
RDF_FINGERPRINTER_FUSEKI_SERVICE = str(RDF_FINGERPRINTER_FUSEKI_LOCATION) + ":" + '3030'

RDF_FINGERPRINTER_FUSEKI_USERNAME = os.environ.get('RDF_FINGERPRINTER_FUSEKI_USERNAME', 'admin')
RDF_FINGERPRINTER_FUSEKI_PASSWORD = os.environ.get('RDF_FINGERPRINTER_FUSEKI_PASSWORD', 'admin')
RDF_FINGERPRINTER_FLASK_SECRET_KEY = os.environ.get('RDF_FINGERPRINTER_FLASK_SECRET_KEY', 'secret key')

RDF_FINGERPRINTER_API_LOCATION = os.environ.get('RDF_FINGERPRINTER_API_LOCATION', 'http://fingerprinter-api')
RDF_FINGERPRINTER_API_PORT = os.environ.get('RDF_FINGERPRINTER_API_PORT', 4020)
RDF_FINGERPRINTER_API_SERVICE = str(RDF_FINGERPRINTER_API_LOCATION) + ":" + str(RDF_FINGERPRINTER_API_PORT)

# TODO: discuss about the default values for host names
RDF_FINGERPRINTER_UI_LOCATION = os.environ.get('RDF_FINGERPRINTER_UI_LOCATION', 'http://localhost')
RDF_FINGERPRINTER_UI_PORT = os.environ.get('RDF_FINGERPRINTER_UI_PORT', 8020)
RDF_FINGERPRINTER_UI_SERVICE = str(RDF_FINGERPRINTER_UI_LOCATION) + ":" + str(RDF_FINGERPRINTER_UI_PORT)


class FlaskConfig:
    """
    Base Flask config
    """
    DEBUG = False
    TESTING = False


class ProductionConfig(FlaskConfig):
    """
    Production Flask config
    """


class DevelopmentConfig(FlaskConfig):
    """
    Development Flask config
    """
    DEBUG = True


class TestingConfig(FlaskConfig):
    """
    Testing Flask config
    """
    TESTING = True
    WTF_CSRF_ENABLED = False
