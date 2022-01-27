import logging as logger
import shutil
from pathlib import Path
from typing import Union
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def build_secure_filename(location: str, filename: str) -> str:
    return str(Path(location) / (str(uuid4()) + secure_filename(filename)))


def copy_file_to_destination(file: str, destination: str) -> str:
    """
    Copy file helper method
    :param file: file to copy
    :param destination: destination to copy
    :return: new file destination
    """
    return shutil.copy(file, destination)


def save_file(file_to_save: FileStorage, location_to_save: Union[str, Path], file_name: str = ''):
    """
    method to save file to permanent storage
    :param file_to_save: file received from request
    :param location_to_save: location to save file
    :param file_name: save file with specified name
    :return: saved file location
    """

    if not location_to_save:
        raise TypeError("Location can't be null")

    if not file_to_save:
        raise TypeError("File cannot be of None type.")

    try:
        saved_file = build_secure_filename(str(location_to_save), file_name or file_to_save.filename)
        file_to_save.save(str(saved_file))
        return saved_file

    except Exception as e:
        logger.error(str(e))
        raise ValueError(str(e))
