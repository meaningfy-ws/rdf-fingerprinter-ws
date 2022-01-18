#!/usr/bin/python3

# config.py
# Date:  14/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Project wide configuration file.
"""

import logging
import os
from distutils.util import strtobool
from pathlib import Path

RDF_FINGERPRINTER_LOGGER = 'fingerprinter'

class FingerprinterConfig:
    logger_name = 'gunicorn.error'
    logger = logging

    @property
    def RDF_FINGERPRINTER_LOGGER(self) -> str:
        value = self.logger_name
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_DEBUG(self) -> bool:
        value = strtobool(os.environ.get('RDF_FINGERPRINTER_DEBUG', 'true'))
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_TEMPLATE_LOCATION(self) -> str:
        if os.environ.get('RDF_FINGERPRINTER_TEMPLATE_LOCATION') \
                and Path(os.environ.get('RDF_FINGERPRINTER_TEMPLATE_LOCATION')).exists() \
                and any(Path(os.environ.get('RDF_FINGERPRINTER_TEMPLATE_LOCATION')).iterdir()):
            value = os.environ.get('RDF_FINGERPRINTER_TEMPLATE_LOCATION')
        else:
            value = None
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_API_SERVICE(self) -> str:
        location = os.environ.get('RDF_FINGERPRINTER_API_LOCATION', 'http://fingerprinter-api')
        port = os.environ.get('RDF_FINGERPRINTER_API_PORT', 4020)
        value = f'{location}:{port}'
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_UI_SERVICE(self) -> str:
        location = os.environ.get('RDF_FINGERPRINTER_UI_LOCATION', 'http://fingerprinter-ui')
        port = os.environ.get('RDF_FINGERPRINTER_UI_PORT', 8020)
        value = f'{location}:{port}'
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_FUSEKI_SERVICE(self) -> str:
        location = os.environ.get('RDF_FINGERPRINTER_FUSEKI_LOCATION', 'http://fuseki')
        port = os.environ.get('RDF_FINGERPRINTER_FUSEKI_PORT', 3030)
        value = f'{location}:{port}'
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_REDIS_SERVICE(self) -> str:
        location = os.environ.get('RDF_FINGERPRINTER_REDIS_LOCATION', 'redis://redis')
        port = os.environ.get('RDF_FINGERPRINTER_REDIS_PORT', 6379)
        value = f'{location}:{port}'
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_FUSEKI_USERNAME(self) -> str:
        value = os.environ.get('RDF_FINGERPRINTER_FUSEKI_USERNAME', 'admin')
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_FUSEKI_PASSWORD(self) -> str:
        value = os.environ.get('RDF_FINGERPRINTER_FUSEKI_PASSWORD', 'admin')
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_API_SECRET_KEY(self) -> str:
        value = os.environ.get('RDF_FINGERPRINTER_API_SECRET_KEY', 'secret key api')
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_UI_SECRET_KEY(self) -> str:
        value = os.environ.get('RDF_FINGERPRINTER_UI_SECRET_KEY', 'secret key ui')
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_TIME_FORMAT(self) -> str:
        value = os.environ.get('RDF_FINGERPRINTER_TIME_FORMAT', '%d-%b-%YT%H:%M:%S')
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_TIMEZONE(self) -> str:
        value = os.environ.get('RDF_FINGERPRINTER_TIMEZONE', 'Europe/Paris')
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_REPORT_META_NAME(self) -> str:
        value = os.environ.get('RDF_FINGERPRINTER_REPORT_META_NAME', 'meta.json')
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_HTML_REPORT_NAME(self) -> str:
        value = os.environ.get('RDF_FINGERPRINTER_HTML_REPORT_NAME', 'report.html')
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_JSON_REPORT_NAME(self) -> str:
        value = os.environ.get('RDF_FINGERPRINTER_JSON_REPORT_NAME', 'report.json')
        self.logger.debug(value)
        return value


config = FingerprinterConfig()


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
