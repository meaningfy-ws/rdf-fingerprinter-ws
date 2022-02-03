from datetime import datetime

from pytz import timezone

from fingerprinter.config import config


def get_timestamp() -> str:
    """
    generate a string timestamp based on the project's time format
    :return: timestamp
    """
    return datetime.now(tz=timezone(config.RDF_FINGERPRINTER_TIMEZONE)).strftime(config.RDF_FINGERPRINTER_TIME_FORMAT)
