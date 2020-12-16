#!/usr/bin/python3

# forms.py
# Date:  22/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Form classes for use in views.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired


class BaseFingerprintForm(FlaskForm):
    graphs = TextAreaField('Graphs', description='Separate them through spaces. example: graph1 graph2')


class FingerprintSPARQLEndpointForm(BaseFingerprintForm):
    sparql_endpoint_url = StringField('Endpoint URL', validators=[DataRequired()])


class FingerprintFileForm(BaseFingerprintForm):
    data_file = FileField('Data file', validators=[FileRequired()])
