#!/usr/bin/python3

# run.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
UI server through flask definitions.
"""

import logging
import os

from fingerprinter.config import DevelopmentConfig, ProductionConfig, config
from fingerprinter.entrypoints.ui import app
from fingerprinter.logging_setup import configure_logging

configure_logging(os.environ.get("RDF_FINGERPRINTER_LOG_LEVEL", "info"))

if config.RDF_FINGERPRINTER_DEBUG:
    app.config.from_object(DevelopmentConfig())
else:
    app.config.from_object(ProductionConfig())

if __name__ == "__main__":
    app.run()

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
