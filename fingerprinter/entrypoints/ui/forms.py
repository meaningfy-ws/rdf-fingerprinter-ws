"""Form classes for the New job page."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired

from fingerprinter.entrypoints.ui import labels


class FingerprintSPARQLEndpointForm(FlaskForm):
    sparql_endpoint_url = StringField(
        "SPARQL endpoint URL",
        description="The query endpoint, for example http://localhost:3030/dataset/sparql.",
        validators=[DataRequired(message=labels.PROBLEMS["InvalidSource"])],
    )
    graphs = TextAreaField(
        "Named graphs (optional)",
        description="One graph IRI per line, or separated by spaces. "
        "Leave empty to profile every graph, including the default graph.",
    )


class FingerprintFileForm(FlaskForm):
    data_file = FileField("RDF file", validators=[FileRequired(message=labels.CHOOSE_A_FILE)])
