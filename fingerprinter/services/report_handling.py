#!/usr/bin/python3

# report_handlers.py
# Date:  22/1/2022
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Service layer for report generation.
"""
import logging
import shutil
from json import dumps, loads
from pathlib import Path
from typing import List
from uuid import uuid4
from zipfile import ZipFile

import requests
from fingerprint.service_layer.handlers import generate_endpoint_fingerprint_report
from werkzeug.utils import secure_filename

from fingerprinter.adapters.sparql_adapter import AbstractSPARQLAdapter, FusekiSPARQLAdapter
from fingerprinter.config import config
from fingerprinter.services.file import copy_file_to_destination, list_folder_paths_from_path, list_folders_from_path
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
    zip_location = str(Path(output_location) / zip_report_name)
    with ZipFile(zip_location, 'w') as zip_report:
        zip_report.write(html_report, arcname=html_report_name)
        zip_report.write(json_report, arcname=json_report_name)
    return zip_location


def copy_report_files(uid: str, html_report: str, json_report: str, zip_report: str,
                      html_report_name: str = '', json_report_name: str = '', zip_report_name: str = '') -> Path:
    """
    Method to copy reports from temporary director to the reports location
    :param uid: uid of the fingerprinting
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
        config.EXTENSION_TO_FILETYPE[config.HTML_REPORT_TYPE]: html_report,
        "file": file_name,
        "url": url,
        "graphs": graphs,
        config.EXTENSION_TO_FILETYPE[config.JSON_REPORT_TYPE]: json_report,
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


def fingerprint_sparql_endpoint(sparql_endpoint: str, output_location: str, graphs: List = None) -> tuple:
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
    :param location: location for the report to be built in
    :param sparql_endpoint: SPARQL endpoint for querying the triplestore service
    :param graphs: (optional) restrict the fingerprinting calculation to this graph
    :param uid: fingerprinting unique identifier
    :return:
    """
    logger.debug('start build report from sparql endpoint library call')
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


def build_report_from_file(location: str, file: str, graphs: list = None, uid: str = '',
                           fuseki_service_location: str = config.RDF_FINGERPRINTER_FUSEKI_SERVICE,
                           fuseki_sparql_adapter: AbstractSPARQLAdapter = None) -> str:
    """
    Build reports from file using the fingerprinter
    :param location: location for the report to be built in
    :param file: file to be fingerprinted
    :param graphs: (optional) restrict the fingerprinting calculation to this graph
    :param uid: fingerprinting unique identifier
    :param fuseki_service_location: fuseki service location
    :param fuseki_sparql_adapter: sparql adapter to be used
    :return: the report location
    """
    logger.debug('start build report from file library call')

    if not fuseki_sparql_adapter:
        fuseki_sparql_adapter = FusekiSPARQLAdapter

    if not graphs:
        graphs = []

    fingerprinting_uid = uid or str(uuid4())
    timestamp = get_timestamp()

    # UPDATE rdf-fingerprinter to accept additional config
    additional_config = {
        "conf": {
            "timestamp": timestamp,
            "title": config.RDF_FINGERPRINTER_REPORT_TITLE
        }
    }

    dataset_uid = str(uuid4())
    sparql_adapter = fuseki_sparql_adapter(fuseki_service_location, requests)

    with upload_file_to_dataset(dataset=dataset_uid, file_path=file, sparql_adapter=sparql_adapter):
        sparql_endpoint = f'{fuseki_service_location}/{dataset_uid}/sparql'
        html_report, json_report, zip_report = fingerprint_sparql_endpoint(sparql_endpoint=sparql_endpoint,
                                                                           output_location=location, graphs=graphs)

    reports_location = copy_report_files(uid=fingerprinting_uid, html_report=html_report, json_report=json_report,
                                         zip_report=zip_report)

    generate_meta_file(reports_location=reports_location, url=sparql_endpoint, uid=fingerprinting_uid,
                       timestamp=timestamp, validation_on='file', graphs=graphs, zip_report=zip_report)

    return str(reports_location)


def build_fingerprinting_reports_location(fingerprinting_uid: str, db_location: str) -> str:
    """
    method to search for report based on the fingerprinting id
    :param fingerprinting_uid: uid of the fingerprinting
    :param db_location: which file system location to use to perform the action
    :return: location of reports
    """
    for location in list_folders_from_path(Path(db_location)):
        content = read_meta_file(Path(db_location) / location)
        if content.get('uid', None) == fingerprinting_uid:
            return str(Path(db_location) / location)

    return ''


def get_available_fingerprintings(reports_location: str = config.RDF_FINGERPRINTER_REPORTS_DB) -> list:
    """
    Get the available fingerprintings
    :param reports_location: location of the reports
    :return: list of available fingerprintings
    """
    logger.debug('start get available fingerprintings library call')
    reports = list()
    for location in list_folder_paths_from_path(Path(reports_location)):
        reports.append(read_meta_file(str(location)))

    logger.debug(f'found {len(reports)} fingerprintings')
    return reports


def get_report(uid: str, extension: str = config.DEFAULT_REPORT_TYPE,
               reports_location: str = config.RDF_FINGERPRINTER_REPORTS_DB) -> tuple:
    report_base_location = build_fingerprinting_reports_location(fingerprinting_uid=uid, db_location=reports_location)
    meta = read_meta_file(report_base_location)
    filename = secure_filename(f"{meta['uid']}-{meta['created_at']}.{extension}")

    return Path(report_base_location) / meta[config.EXTENSION_TO_FILETYPE[extension]], filename


def delete_report(uid: str, reports_location: str = config.RDF_FINGERPRINTER_REPORTS_DB) -> bool:
    """
    Remove the report
    :param uid: uid of the fingerprinting reports to be removed
    :param reports_location: location of the reports
    :return: True if the report was removed, False otherwise
    """
    logger.debug('start remove report library call')
    report_location = build_fingerprinting_reports_location(fingerprinting_uid=uid, db_location=reports_location)

    if report_location:
        shutil.rmtree(report_location)
        return True

    return False


def delete_all_reports(reports_location: str = config.RDF_FINGERPRINTER_REPORTS_DB) -> bool:
    """
    Remove all reports
    :param reports_location: location of the reports
    :return: True if the reports were removed, False otherwise
    """
    logger.debug('start remove all reports library call')
    try:
        for location in list_folder_paths_from_path(Path(reports_location)):
            shutil.rmtree(str(location))
        return True
    except Exception:
        logger.exception('error removing all reports')
        return False