"""The composition root: reads the settings, builds the adapters and services, exposes the apps.

* API:    ``gunicorn --worker-class uvicorn_worker.UvicornWorker 'fingerprinter.bootstrap:api_app()'``
* UI:     ``gunicorn 'fingerprinter.bootstrap:ui_app()'``
* worker: ``celery -A fingerprinter.bootstrap:celery_app worker``
"""

import functools
import logging

from celery import Celery
from connexion import FlaskApp
from flask import Flask

from fingerprinter.adapters.celery_queue import CeleryJobQueue
from fingerprinter.adapters.file_job_store import FileJobStore
from fingerprinter.adapters.file_upload_store import FileUploadStore
from fingerprinter.adapters.fingerprint_library import LibraryFingerprinter
from fingerprinter.adapters.fuseki import FusekiDatasetStore
from fingerprinter.adapters.plantuml import PlantUmlRenderer
from fingerprinter.config import Settings, require_secret
from fingerprinter.entrypoints.api import create_app as create_api_app
from fingerprinter.entrypoints.ui import create_app as create_ui_app
from fingerprinter.entrypoints.worker.tasks import register_tasks
from fingerprinter.services.ports import Services

settings = Settings.from_env()

# No result backend: a job's state is its record (design D-5). A downed Redis fails a submission in
# about a second, so the API answers 503 instead of hanging.
celery_app = Celery("rdf-fingerprinter", broker=settings.redis_url)
celery_app.conf.update(
    task_publish_retry_policy={"max_retries": 1, "interval_start": 0},
    broker_connection_timeout=1,
    broker_connection_retry_on_startup=True,
)


@functools.cache
def build_services() -> Services:
    """The adapters and services, built on first use: the UI process never asks for them."""
    return Services(
        job_store=FileJobStore(settings.reports_db),
        upload_store=FileUploadStore(settings.file_db, settings.max_upload_bytes),
        queue=CeleryJobQueue(celery_app),
        dataset_store=FusekiDatasetStore(
            settings.fuseki_url,
            settings.fuseki_user,
            settings.fuseki_password,
            settings.input_mime_types,
        ),
        fingerprinter=LibraryFingerprinter(),
        diagram_renderer=PlantUmlRenderer(settings.plantuml_url),
        supported_extensions=frozenset(settings.input_mime_types),
        output_mime_types=settings.output_mime_types,
    )


register_tasks(celery_app, build_services)


def _configure_logging() -> None:
    """Send the service's own log records to stdout at the configured level."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s %(message)s"))
    service_logger = logging.getLogger("fingerprinter")
    service_logger.handlers = [handler]
    service_logger.setLevel(settings.log_level.upper())
    service_logger.propagate = False


def api_app() -> FlaskApp:
    _configure_logging()
    app = create_api_app(build_services(), swagger_ui=settings.show_swagger_ui)
    app.app.config["SECRET_KEY"] = require_secret(
        "RDF_FINGERPRINTER_API_SECRET_KEY", settings.api_secret_key
    )
    return app


def ui_app() -> Flask:
    _configure_logging()
    return create_ui_app(
        settings.api_url,
        require_secret("RDF_FINGERPRINTER_UI_SECRET_KEY", settings.ui_secret_key),
        accepted_extensions=tuple(sorted(settings.input_mime_types)),
        max_upload_bytes=settings.max_upload_bytes,
        secure_cookies=settings.ui_secure_cookies,
    )
