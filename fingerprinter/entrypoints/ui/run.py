#!/usr/bin/python3

# run.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
UI server through flask definitions.
"""
import logging

from fingerprinter.config import RDF_FINGERPRINTER_DEBUG, ProductionConfig, DevelopmentConfig
from fingerprinter.entrypoints.ui import app

if RDF_FINGERPRINTER_DEBUG:
    app.config.from_object(DevelopmentConfig())
else:
    app.config.from_object(ProductionConfig())

if __name__ == '__main__':
    app.run()

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
