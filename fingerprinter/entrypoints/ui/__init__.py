#!/usr/bin/python3

# __init__.py
# Date:  14/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Module for configuring and exposing the ui server using the Flask framework.
"""

from flask import Flask

from fingerprinter.entrypoints.flask_config import FLASK_SECRET_KEY

app = Flask(__name__)

app.config['SECRET_KEY'] = FLASK_SECRET_KEY

from . import views
