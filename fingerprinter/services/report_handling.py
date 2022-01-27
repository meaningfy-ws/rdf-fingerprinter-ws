#!/usr/bin/python3

# report_handlers.py
# Date:  22/1/2022
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Service layer for report generation.
"""
import logging
import uuid
from json import dumps, loads
from pathlib import Path
from typing import List
from uuid import uuid4
from zipfile import ZipFile

from fingerprint.service_layer.handlers import generate_endpoint_fingerprint_report
from werkzeug.utils import secure_filename

from fingerprinter.adapters.sparql_adapter import AbstractSPARQLAdapter
from fingerprinter.config import config
from fingerprinter.services.file import copy_file_to_destination
from fingerprinter.services.handlers import upload_file_to_dataset
from fingerprinter.services.time import get_timestamp

logger = logging


def zip_report_files(output_location: str, html_report: str, json_report: str, html_report_name: str = '',
                     json_report_name: str = '', zip_report_name: str = '') -> str:
    """
    Method to zip files
    :param output_location: location to create zip
    :param html_report: html report location
    :param json_report: ttl report location
    :param html_report_name: html report name
    :param json_report_name: json report name
    :param zip_report_name: zip report name
    :return: location of the zip
    """

    html_report_name = html_report_name or config.RDF_FINGERPRINTER_HTML_REPORT_NAME
    json_report_name = json_report_name or config.RDF_FINGERPRINTER_JSON_REPORT_NAME
    zip_report_name = zip_report_name or config.RDF_FINGERPRINTER_ZIP_REPORT_NAME

    logger.debug('zipping report')
    zip_location = str(Path(output_location) / html_report_name)
    with ZipFile(zip_location, 'w') as zip_report:
        zip_report.write(html_report, arcname=json_report_name)
        zip_report.write(json_report, arcname=zip_report_name)
    return zip_location


def copy_report_files(uid: str, html_report: str, json_report: str, zip_report: str,
                      html_report_name: str = '', json_report_name: str = '', zip_report_name: str = '') -> Path:
    """
    Method to copy reports from temporary director to the reports location
    :param uid: uid of the validation
    :param html_report: html report location
    :param json_report: ttl report location
    :param zip_report: zip location containing all reports
    :param html_report_name: html report name
    :param json_report_name: json report name
    :param zip_report_name: zip report name
    :return: location of copied reports
    """
    reports_location = Path(config.RDF_FINGERPRINTER_REPORTS_DB) / secure_filename(uid)
    reports_location.mkdir()

    html_report_name = html_report_name or config.RDF_FINGERPRINTER_HTML_REPORT_NAME
    json_report_name = json_report_name or config.RDF_FINGERPRINTER_JSON_REPORT_NAME
    zip_report_name = zip_report_name or config.RDF_FINGERPRINTER_ZIP_REPORT_NAME

    copy_file_to_destination(html_report, str(reports_location / html_report_name))
    copy_file_to_destination(json_report, str(reports_location / json_report_name))
    copy_file_to_destination(zip_report, str(reports_location / zip_report_name))
    return reports_location


def generate_meta_file(reports_location: Path, file_name: str = '', url: str = '', uid: str = '',
                       timestamp: str = '', validation_on: str = 'file', html_report: str = '', json_report: str = '',
                       zip_report: str = '',
                       graphs: list = None) -> str:
    """
    method to generate meta file

    :param reports_location: location of fingerprinting reports
    :param file_name: the name of the file to be fingerprinted
    :param url: the name of the sparql endpoint to be fingerprinted
    :param uid: fingerprinting unique identifier
    :param timestamp: timestamp of fingerprinting creation
    :param validation_on: file or url
    :param html_report: name of the html report
    :param json_report: name of the json report
    :param zip_report: name of the zip containing all reports
    :param graphs: the URIs of the graphs
    :return: location of meta file
    """
    timestamp = timestamp or get_timestamp()
    html_report = html_report or config.RDF_FINGERPRINTER_HTML_REPORT_NAME
    json_report = json_report or config.RDF_FINGERPRINTER_JSON_REPORT_NAME
    zip_report = zip_report or config.RDF_FINGERPRINTER_ZIP_REPORT_NAME

    meta = {
        "uid": uid or str(uuid4()),
        "validation_on": validation_on,
        "html_report": html_report,
        "file": file_name,
        "url": url,
        "graphs": graphs,
        "json_report": json_report,
        "zip_report": zip_report,
        "created_at": timestamp
    }

    meta_file = reports_location / config.RDF_FINGERPRINTER_REPORT_META_NAME
    meta_file.write_text(dumps(meta))
    return str(meta_file)


def read_meta_file(report_base_location: str, meta_file_name: str = '') -> dict:
    """
    method to read data from meta file
    :param report_base_location: report location
    :param meta_file_name: custom meta name, defaults to "meta.json"
    :return: contents of the meta file
    """
    meta_file_name = meta_file_name or config.RDF_FINGERPRINTER_REPORT_META_NAME
    return loads((Path(report_base_location) / meta_file_name).read_text())


def fingerprint_sparql_endpoint(sparql_endpoint: str, output_location: str, graphs: List = None) -> str:
    """
        Fingerprint a SPARQL endpoint using the fingerprinter
        available at https://github.com/meaningfy-ws/rdf-fingerprinter.
    :param sparql_endpoint: SPARQL endpoint for querying the triplestore service
    :param output_location: location for the report to be built in
    :param graphs: (optional) restrict the fingerprinting calculation to this graph
    :return: the report location
    """
    logger.debug('generating fingerprinting reports')

    html_report = str(generate_endpoint_fingerprint_report(
        sparql_endpoint_url=sparql_endpoint, output_location=output_location, selected_graphs=graphs,
        external_template_location=config.RDF_FINGERPRINTER_HTML_TEMPLATE_LOCATION
    ))

    json_report = str(generate_endpoint_fingerprint_report(
        sparql_endpoint_url=sparql_endpoint, output_location=output_location, selected_graphs=graphs,
        external_template_location=config.RDF_FINGERPRINTER_JSON_TEMPLATE_LOCATION
    ))

    zip_report = zip_report_files(output_location=output_location, html_report=html_report, json_report=json_report)

    logger.debug('finish generating fingerprinting reports')
    return html_report, json_report, zip_report


def build_report_from_sparql_endpoint(location: str, sparql_endpoint: str, graphs: List = None, uid: str = '') -> str:
    """
    Build a report from a SPARQL endpoint using the fingerprinter
    available at
    :param location:
    :param sparql_endpoint:
    :param graphs:
    :param uid:
    :return:
    """
    logger.debug('start build report from sparql endpoint library call')
    logger.debug('start building report from file')
    uid = uid or str(uuid4())
    timestamp = get_timestamp()

    additional_config = {
        "conf": {
            "timestamp": timestamp,
            "title": config.RDF_FINGERPRINTER_REPORT_TITLE
        }
    }
    html_report, json_report, zip_report = fingerprint_sparql_endpoint(sparql_endpoint=sparql_endpoint,
                                                                       output_location=location, graphs=graphs)

    reports_location = copy_report_files(uid=uid, html_report=html_report, json_report=json_report,
                                         zip_report=zip_report)

    generate_meta_file(reports_location=reports_location, url=sparql_endpoint, uid=uid, timestamp=timestamp,
                       validation_on='sparql_endpoint', graphs=graphs, html_report=html_report, json_report=json_report,
                       zip_report=zip_report)

    return str(reports_location)

def fingerprint_file(file_path: str, output_location: str, sparql_adapter: AbstractSPARQLAdapter,
                         graphs: List = None) -> str:
    """
        Fingerprint a file using the fingerprinter available at https://github.com/meaningfy-ws/rdf-fingerprinter.
    :param file_path: file to be fingerprinted
    :param output_location: location for the report to be built in
    :param sparql_adapter: adapter used to perform triplestore operations
    :param graphs: (optional) restrict the fingerprinting calculation to this graph
    :return:
    """

    logger.debug('start fingerprint file library call')

    dataset_name = str(uuid.uuid4())

    with upload_file_to_dataset(dataset_name, file_path, sparql_adapter):
        sparql_endpoint = f'{config.RDF_FINGERPRINTER_FUSEKI_SERVICE}/{dataset_name}/query'
        report_path = fingerprint_sparql_endpoint(sparql_endpoint, output_location, graphs)

    logger.debug('end fingerprint file library call')
    return report_path
