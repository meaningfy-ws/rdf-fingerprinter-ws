#!/usr/bin/python3

# commands.py
# Date:  23/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import requests
from pathlib import Path

from fingerprinter import config
from fingerprinter.adapters.sparql_adapter import FusekiSPARQLAdapter


def populate_fuseki():
    adapter = FusekiSPARQLAdapter(config.RDF_FINGERPRINTER_FUSEKI_SERVICE, requests)
    adapter.create_dataset('test-dataset')
    file_path = Path(__file__).parents[1] / 'tests/resources/treaties-source-api.rdf'
    adapter.upload_file('test-dataset', file_path)


if __name__ == '__main__':
    populate_fuseki()
