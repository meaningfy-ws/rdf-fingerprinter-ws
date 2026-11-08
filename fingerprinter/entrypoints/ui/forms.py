"""Form classes for the New job page."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired

from fingerprinter.entrypoints.ui import labels


class FingerprintSPARQLEndpointForm(FlaskForm):
    sparql_endpoint_url = StringField(
        labels.ENDPOINT_URL_LABEL,
        description=labels.ENDPOINT_URL_HELP,
        validators=[DataRequired(message=labels.PROBLEMS["InvalidSource"])],
    )
    graphs = TextAreaField(labels.GRAPHS_LABEL, description=labels.GRAPHS_HELP)


class FingerprintFileForm(FlaskForm):
    data_file = FileField(
        labels.FILE_LABEL, validators=[FileRequired(message=labels.CHOOSE_A_FILE)]
    )
