import logging as logger
import shutil

from celery import Celery

from fingerprinter.config import config
from fingerprinter.services.report_handling import build_report_from_sparql_endpoint, build_report_from_file

celery_worker = Celery('rdf-fingerprinter-tasks',
                       broker=config.RDF_FINGERPRINTER_REDIS_SERVICE,
                       backend=config.RDF_FINGERPRINTER_REDIS_SERVICE)
celery_worker.conf.update(result_extended=True)

CELERY_FINGERPRINT_URL = 'fingerprint_url'
CELERY_FINGERPRINT_FILE = 'fingerprint_file'


@celery_worker.task(name=CELERY_FINGERPRINT_URL, bind=True)
def async_fingerprint_sparql_endpoint(self, sparql_endpoint_url: str, db_cleanup_location: str, graphs: list = None):
    """
    Task to fingeprint a SPARQL endpoint

    :param sparql_endpoint_url: The SPARQL endpoint to be fingerprinted
    :param db_cleanup_location: location to cleanup
    :param graphs: list of optional graphs to fingerprint
    """
    logger.info('Starting async_fingerprint_sparql_endpoint')

    report_path = build_report_from_sparql_endpoint(location=db_cleanup_location, sparql_endpoint=sparql_endpoint_url,
                                                    graphs=graphs, uid=self.request.id)

    shutil.rmtree(db_cleanup_location)
    logger.info(f'Report generated at {report_path}')
    return report_path


@celery_worker.task(name=CELERY_FINGERPRINT_FILE, bind=True)
def async_fingerprint_file(self, file_path: str, db_cleanup_location: str, graphs: list = None):
    """
    Task to fingeprint a file

    :param file_path: The file to be fingerprinted
    :param db_cleanup_location: location to cleanup
    :param graphs: list of optional graphs to fingerprint
    """
    logger.info('Starting async_fingerprint_file')

    report_path = build_report_from_file(location=db_cleanup_location, file=file_path, graphs=graphs,
                                         uid=self.request.id)

    shutil.rmtree(db_cleanup_location)
    logger.info(f'Report generated at {report_path}')
    return report_path
