import logging as logger
import shutil

from celery import Celery

from fingerprinter.config import config

celery_worker = Celery('rdf-fingerprinter-tasks',
                       broker=config.RDF_FINGERPRINTER_REDIS_SERVICE,
                       backend=config.RDF_FINGERPRINTER_REDIS_SERVICE)
celery_worker.conf.update(result_extended=True)

CELERY_VALIDATE_FILE = 'validate_file'
CELERY_VALIDATE_URL = 'validate_url'


@celery_worker.task(name=CELERY_VALIDATE_FILE, bind=True)
def async_validate_file(self, uid: str, data_file: str, shacl_shapes: list, db_cleanup_location: str,
                        application_profile: str = ''):
    """
    Task that to validate a file

    NOTE: the order of the first arg is important for task cancellation, don't change its order
    :param uid: validation identifier
    :param data_file: The file to be validated
    :param shacl_shapes: The content of the SHACL shape files defining the validation constraints
    :param db_cleanup_location: location to cleanup
    :param application_profile: application profile if provided
    """