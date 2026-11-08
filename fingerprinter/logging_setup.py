"""Logging for the API and UI processes (the Celery worker configures its own)."""

import logging


def configure_logging(level: str) -> None:
    """Send the service's own log records to stdout at `level` (e.g. "debug", "info")."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s %(message)s"))
    service_logger = logging.getLogger("fingerprinter")
    service_logger.handlers = [handler]
    service_logger.setLevel(level.upper())
    service_logger.propagate = False
