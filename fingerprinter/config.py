#!/usr/bin/python3

# config.py
# Date:  14/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Project wide configuration file.
"""

import os

FINGERPRINTER_DEBUG = os.environ.get('FINGERPRINTER_DEBUG')

FUSEKI_PORT = os.environ.get('FUSEKI_PORT', 3030)
FUSEKI_LOCATION = os.environ.get('FUSEKI_LOCATION', 'http://localhost')
FUSEKI_SERVICE = str(FUSEKI_PORT) + ":" + str(FUSEKI_LOCATION)

FUSEKI_USERNAME = os.environ.get('FUSEKI_USERNAME', 'admin')
FUSEKI_PASSWORD = os.environ.get('FUSEKI_PASSWORD', 'admin')
