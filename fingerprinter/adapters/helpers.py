#!/usr/bin/python3

# helpers.py
# Date:  18/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from pathlib import PurePath

from fingerprinter.config import config


def get_file_format(file: str, types: dict[str, str] | None = None) -> str:
    """
    Helper method to check get the format of the provided file, and to check whether they are from the
    acceptable file formats.
    :param file: file location
    :param types: a dictionary of expected fle types for the file to be checked on
    :return: format of the file
    """
    file_format = (config.INPUT_MIME_TYPES if types is None else types).get(
        PurePath(str(file)).suffix.lstrip(".").lower()
    )
    if file_format is None:
        raise ValueError(f'Format of "{file}" is not supported.')

    return file_format
