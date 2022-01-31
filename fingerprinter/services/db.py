import logging as logger
from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage

from fingerprinter.config import config
from fingerprinter.services.file import save_file


def create_db_entry(location: str = config.RDF_FINGERPRINTER_FILE_DB) -> str:
    location_to_save = Path(location) / str(uuid4())
    location_to_save.mkdir()
    return str(location_to_save)


def save_file_for_fingerprinting(file_to_fingerprint: FileStorage,
                                 location_to_save: str) -> str:
    """
    Save a file to the database.
    :param file_to_fingerprint: FileStorage object
    :param location_to_save: str
    :return: str
    """

    try:
        saved_file_to_fingerprint = save_file(file_to_fingerprint, location_to_save)
    except TypeError:
        saved_file_to_fingerprint = None
        logger.debug('no file to save')

    return saved_file_to_fingerprint
