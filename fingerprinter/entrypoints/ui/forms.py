#!/usr/bin/python3

# forms.py
# Date:  22/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

""" """
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField
from wtforms.validators import DataRequired


class BaseFingerprintForm(FlaskForm):
    graph = StringField('Graph', description='A named graph to restrict the fingerprint calculation to')


class FingerprintSPARQLEndpointForm(BaseFingerprintForm):
    sparql_endpoint_url = StringField('Endpoint URL', validators=[DataRequired()])


class FingerprintFileForm(BaseFingerprintForm):
    data_file = FileField('Data file', validators=[FileRequired()])
