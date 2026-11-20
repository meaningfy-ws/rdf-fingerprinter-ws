"""The composition root: it builds the adapters and services from the settings."""

import importlib
import logging
import sys
import time

import pytest
from celery.backends.base import DisabledBackend
from connexion import FlaskApp
from flask import Flask

from fingerprinter.adapters.celery_queue import CeleryJobQueue
from fingerprinter.adapters.file_job_store import FileJobStore
from fingerprinter.adapters.fingerprint_library import LibraryFingerprinter
from fingerprinter.adapters.fuseki import FusekiDatasetStore
from fingerprinter.adapters.plantuml import PlantUmlRenderer
from fingerprinter.services.ports import Services


@pytest.fixture
def bootstrap(monkeypatch):
    """A fresh import of ``fingerprinter.bootstrap``, which reads the environment when imported."""
    monkeypatch.setenv("RDF_FINGERPRINTER_API_SECRET_KEY", "api-secret")
    monkeypatch.setenv("RDF_FINGERPRINTER_UI_SECRET_KEY", "ui-secret")
    monkeypatch.setenv("RDF_FINGERPRINTER_REDIS_LOCATION", "redis://localhost")
    monkeypatch.setenv("RDF_FINGERPRINTER_REDIS_PORT", "1")  # nothing listens: a submission fails
    monkeypatch.delitem(sys.modules, "fingerprinter.bootstrap", raising=False)
    return importlib.import_module("fingerprinter.bootstrap")


@pytest.mark.parametrize(
    ("kept", "built", "refused"),
    [("UI", "ui_app", "api_app"), ("API", "api_app", "ui_app")],
)
def test_each_app_needs_only_its_own_secret_key(bootstrap, monkeypatch, kept, built, refused):
    monkeypatch.delenv(
        "RDF_FINGERPRINTER_API_SECRET_KEY" if kept == "UI" else "RDF_FINGERPRINTER_UI_SECRET_KEY"
    )
    bootstrap = importlib.reload(bootstrap)
    missing = "API" if kept == "UI" else "UI"

    assert getattr(bootstrap, built)() is not None
    with pytest.raises(ValueError, match=f"RDF_FINGERPRINTER_{missing}_SECRET_KEY must be set"):
        getattr(bootstrap, refused)()


def test_the_celery_app_has_the_redis_broker_and_no_result_backend(bootstrap):
    app = bootstrap.celery_app

    assert app.conf.broker_url == "redis://localhost:1"
    assert isinstance(app.backend, DisabledBackend)


def test_the_worker_tasks_are_registered_without_building_the_adapters(bootstrap):
    assert {"fingerprint_endpoint", "fingerprint_file"} <= set(bootstrap.celery_app.tasks)
    assert bootstrap.build_services.cache_info().currsize == 0


def test_a_submission_fails_fast_when_the_broker_is_down(bootstrap):
    started = time.monotonic()

    with pytest.raises(Exception, match="Connection refused|connect"):
        bootstrap.celery_app.send_task("fingerprint_endpoint", args=["j", "http://e/sparql", []])

    assert time.monotonic() - started < 10


def test_the_api_app_serves_the_services_built_from_the_settings(bootstrap):
    app = bootstrap.api_app()

    assert isinstance(app, FlaskApp)
    assert app.app.config["SECRET_KEY"] == "api-secret"
    services = app.app.extensions["fingerprinter"]
    assert isinstance(services, Services)
    assert isinstance(services.job_store, FileJobStore)
    assert isinstance(services.queue, CeleryJobQueue)
    assert services.upload_store.max_bytes == 512 * 1024 * 1024
    assert isinstance(services.dataset_store, FusekiDatasetStore)
    assert isinstance(services.fingerprinter, LibraryFingerprinter)
    assert isinstance(services.diagram_renderer, PlantUmlRenderer)
    assert services.diagram_renderer.base_url == "http://plantuml:8080"
    assert services.supported_extensions == {"rdf", "trix", "nq", "nt", "jsonld", "n3", "ttl"}


@pytest.mark.parametrize(("switch", "status"), [("true", 200), ("false", 404)])
def test_the_swagger_ui_follows_the_setting(bootstrap, monkeypatch, switch, status):
    monkeypatch.setenv("SHOW_SWAGGER_UI", switch)
    bootstrap = importlib.reload(bootstrap)

    assert bootstrap.api_app().test_client().get("/ui/").status_code == status


def test_the_ui_app_is_a_client_of_the_api_with_its_own_secret_key(bootstrap):
    app = bootstrap.ui_app()

    assert isinstance(app, Flask)
    assert app.config["SECRET_KEY"] == "ui-secret"
    assert app.extensions["api"].base_url == "http://fingerprinter-api:4020"


def test_the_ui_app_is_given_the_accepted_extensions_and_the_upload_limit(bootstrap):
    app = bootstrap.ui_app()

    assert app.config["ACCEPTED_EXTENSIONS"] == ("jsonld", "n3", "nq", "nt", "rdf", "trix", "ttl")
    assert app.config["MAX_UPLOAD_BYTES"] == 512 * 1024 * 1024


@pytest.mark.parametrize(("value", "secure"), [("true", True), ("false", False)])
def test_the_ui_session_cookie_is_secure_when_the_setting_says_so(
    bootstrap, monkeypatch, value, secure
):
    monkeypatch.setenv("RDF_FINGERPRINTER_UI_SECURE_COOKIES", value)
    bootstrap = importlib.reload(bootstrap)

    assert bootstrap.ui_app().config["SESSION_COOKIE_SECURE"] is secure


def test_the_ui_process_builds_no_adapters(bootstrap):
    bootstrap.ui_app()

    assert bootstrap.build_services.cache_info().currsize == 0


def test_the_adapters_are_built_once_for_the_api(bootstrap):
    first = bootstrap.api_app().app.extensions["fingerprinter"]
    second = bootstrap.api_app().app.extensions["fingerprinter"]

    assert first is second
    assert bootstrap.build_services.cache_info().currsize == 1


def test_the_service_logs_at_the_configured_level(bootstrap, monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_LOG_LEVEL", "debug")
    bootstrap = importlib.reload(bootstrap)

    bootstrap.api_app()

    assert logging.getLogger("fingerprinter").getEffectiveLevel() == logging.DEBUG
