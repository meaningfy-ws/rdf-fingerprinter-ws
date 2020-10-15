#!/usr/bin/python3

# config.py
# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Configuration for the current Flask project.
"""
import os

FLASK_SECRET_KEY = os.environ.get('SECRET_KEY', 'secret key')
