#!/usr/bin/python3

# helpers.py
# Date:  21/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
API helper methods or constants
"""
from rdflib.util import guess_format

INPUT_MIME_TYPES = {
    'rdf': 'application/rdf+xml',
    'trix': 'application/xml',
    'nq': 'application/n-quads',
    'nt': 'application/n-triples',
    'jsonld': 'application/ld+json',
    'n3': 'text/n3',
    'ttl': 'text/turtle',
}

HTML_REPORT_TYPE = 'html'

REPORT_TYPES = [HTML_REPORT_TYPE]
DEFAULT_REPORT_TYPE = REPORT_TYPES[0]


def _guess_file_type(file: str, accepted_types: dict = None):
    if accepted_types is None:
        accepted_types = INPUT_MIME_TYPES
    return guess_format(str(file), accepted_types)
