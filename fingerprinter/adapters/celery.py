import logging as logger
import shutil

from celery import Celery

from fingerprinter.config import config
from fingerprinter.services.report_handling import build_report_from_sparql_endpoint

celery_worker = Celery('rdf-fingerprinter-tasks',
                       broker=config.RDF_FINGERPRINTER_REDIS_SERVICE,
                       backend=config.RDF_FINGERPRINTER_REDIS_SERVICE)
celery_worker.conf.update(result_extended=True)

CELERY_FINGERPRINT_FILE = 'fingerprint_file'
CELERY_FINGERPRINT_URL = 'fingerprint_url'



@celery_worker.task(name=CELERY_FINGERPRINT_URL, bind=True)
def async_fingerprint_sparql_endpoint(self, sparql_endpoint_url: str, db_cleanup_location: str, graphs: list = None):
    """
    Task to fingeprint a SPARQL endpoint

    NOTE: the order of the first arg is important for task cancellation, don't change its order
    :param sparql_endpoint_url: The SPARQL endpoint to be validated
    :param db_cleanup_location: location to cleanup
    :param graphs: list of optional graphs to validate
    """
    logger.info('Starting async_fingerprint_sparql_endpoint')

    report_path = build_report_from_sparql_endpoint(location=db_cleanup_location, sparql_endpoint=sparql_endpoint_url,
                                                    graphs=graphs, uid=self.request.id)

    shutil.rmtree(db_cleanup_location)
    logger.info('Report generated at {}'.format(report_path))
    return report_path
