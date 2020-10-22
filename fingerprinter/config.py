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
RDF_FINGERPRINTER_FUSEKI_SERVICE = str(RDF_FINGERPRINTER_FUSEKI_LOCATION) + ":" + str(RDF_FINGERPRINTER_FUSEKI_PORT)

RDF_FINGERPRINTER_FUSEKI_USERNAME = os.environ.get('RDF_FINGERPRINTER_FUSEKI_USERNAME', 'admin')
RDF_FINGERPRINTER_FUSEKI_PASSWORD = os.environ.get('RDF_FINGERPRINTER_FUSEKI_PASSWORD', 'admin')
FLASK_SECRET_KEY = os.environ.get('SECRET_KEY', 'secret key')


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
