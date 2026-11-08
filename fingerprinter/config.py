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
from pathlib import Path


def strtobool(value: str) -> bool:
    """The truth value of a setting, as distutils.util.strtobool (removed in Python 3.12) gave it."""
    normalised = value.strip().lower()
    if normalised in ("1", "true", "yes", "on", "y", "t"):
        return True
    if normalised in ("0", "false", "no", "off", "n", "f"):
        return False
    raise ValueError(f"invalid truth value {value!r}")


class FingerprinterConfig:
    """
    Class to hold the configuration for the fingerprinter project.
    """

    logger_name = "gunicorn.error"
    logger = logging

    @property
    def RDF_FINGERPRINTER_LOGGER(self) -> str:
        value = self.logger_name
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_DEBUG(self) -> bool:
        value = strtobool(os.environ.get("RDF_FINGERPRINTER_DEBUG", "true"))
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_API_SERVICE(self) -> str:
        location = os.environ.get("RDF_FINGERPRINTER_API_LOCATION", "http://fingerprinter-api")
        port = os.environ.get("RDF_FINGERPRINTER_API_PORT", 4020)
        value = f"{location}:{port}"
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_UI_SERVICE(self) -> str:
        location = os.environ.get("RDF_FINGERPRINTER_UI_LOCATION", "http://fingerprinter-ui")
        port = os.environ.get("RDF_FINGERPRINTER_UI_PORT", 8020)
        value = f"{location}:{port}"
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_FUSEKI_SERVICE(self) -> str:
        location = os.environ.get("RDF_FINGERPRINTER_FUSEKI_LOCATION", "http://fuseki")
        port = os.environ.get("RDF_FINGERPRINTER_FUSEKI_PORT", 3030)
        value = f"{location}:{port}"
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_REDIS_SERVICE(self) -> str:
        location = os.environ.get("RDF_FINGERPRINTER_REDIS_LOCATION", "redis://redis")
        port = os.environ.get("RDF_FINGERPRINTER_REDIS_PORT", 6379)
        value = f"{location}:{port}"
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_FUSEKI_USERNAME(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_FUSEKI_USERNAME", "")
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_FUSEKI_PASSWORD(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_FUSEKI_PASSWORD", "")
        # a secret: never logged
        return value

    @property
    def RDF_FINGERPRINTER_API_SECRET_KEY(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_API_SECRET_KEY", "secret key api")
        # a secret: never logged
        return value

    @property
    def RDF_FINGERPRINTER_UI_SECRET_KEY(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_UI_SECRET_KEY", "secret key ui")
        # a secret: never logged
        return value

    @property
    def RDF_FINGERPRINTER_TIME_FORMAT(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_TIME_FORMAT", "%d-%b-%YT%H:%M:%S")
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_TIMEZONE(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_TIMEZONE", "Europe/Paris")
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_REPORT_META_NAME(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_REPORT_META_NAME", "meta.json")
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_HTML_REPORT_NAME(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_HTML_REPORT_NAME", "report.html")
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_JSON_REPORT_NAME(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_JSON_REPORT_NAME", "report.json")
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_ZIP_REPORT_NAME(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_ZIP_REPORT_NAME", "report.zip")
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_FILE_DB(self) -> str:
        value = os.environ.get("RDF_FINGERPRINTER_FILE_DB", str(Path(__file__).parents[1] / "db"))
        self.logger.debug(value)
        return value

    @property
    def RDF_FINGERPRINTER_REPORTS_DB(self) -> str:
        value = os.environ.get(
            "RDF_FINGERPRINTER_REPORTS_DB", str(Path(__file__).parents[1] / "reports")
        )
        self.logger.debug(value)
        return value

    @property
    def SHOW_SWAGGER_UI(self) -> bool:
        value = strtobool(os.environ.get("SHOW_SWAGGER_UI", "true"))
        self.logger.debug(value)
        return value

    @property
    def INPUT_MIME_TYPES(self) -> dict:
        value = {
            "rdf": "application/rdf+xml",
            "trix": "application/trix+xml",
            "nq": "application/n-quads",
            "nt": "application/n-triples",
            "jsonld": "application/ld+json",
            "n3": "text/n3",
            "ttl": "text/turtle",
        }
        self.logger.debug(value)
        return value

    @property
    def HTML_REPORT_TYPE(self) -> str:
        value = "html"
        self.logger.debug(value)
        return value

    @property
    def JSON_REPORT_TYPE(self) -> str:
        value = "json"
        self.logger.debug(value)
        return value

    @property
    def ZIP_REPORT_TYPE(self) -> str:
        value = "zip"
        self.logger.debug(value)
        return value

    @property
    def REPORT_TYPES(self) -> list:
        value = [self.HTML_REPORT_TYPE, self.JSON_REPORT_TYPE, self.ZIP_REPORT_TYPE]
        self.logger.debug(value)
        return value

    @property
    def DEFAULT_REPORT_TYPE(self) -> str:
        value: str = self.REPORT_TYPES[0]
        self.logger.debug(value)
        return value

    @property
    def EXTENSION_TO_FILETYPE(self) -> dict:
        value = {
            self.HTML_REPORT_TYPE: "html_report",
            self.JSON_REPORT_TYPE: "json_report",
            self.ZIP_REPORT_TYPE: "zip_report",
        }
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
