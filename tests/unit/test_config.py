import os
from pathlib import Path

import pytest

from fingerprinter.config import Settings, strtobool

API_KEY = "RDF_FINGERPRINTER_API_SECRET_KEY"
UI_KEY = "RDF_FINGERPRINTER_UI_SECRET_KEY"


@pytest.fixture
def env(monkeypatch):
    """An environment holding only the two required secret keys."""
    for name in list(os.environ):
        if name.startswith("RDF_FINGERPRINTER_") or name == "SHOW_SWAGGER_UI":
            monkeypatch.delenv(name)
    monkeypatch.setenv(API_KEY, "api-secret")
    monkeypatch.setenv(UI_KEY, "ui-secret")
    return monkeypatch


@pytest.mark.parametrize("value", ["1", "true", "True", " yes ", "on", "y", "t"])
def test_true_values(value):
    assert strtobool(value) is True


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off", "n", "f"])
def test_false_values(value):
    assert strtobool(value) is False


def test_an_unknown_value_is_an_error():
    with pytest.raises(ValueError, match="ture"):
        strtobool("ture")


def test_the_defaults_are_todays(env):
    settings = Settings.from_env()

    assert settings.api_url == "http://fingerprinter-api:4020"
    assert settings.fuseki_url == "http://fuseki:3030"
    assert settings.redis_url == "redis://redis:6379"
    assert (settings.fuseki_user, settings.fuseki_password) == ("", "")
    assert settings.show_swagger_ui is True
    assert settings.log_level == "info"
    assert settings.file_db.name == "db"
    assert settings.reports_db.name == "reports"
    assert settings.api_secret_key == "api-secret"
    assert settings.ui_secret_key == "ui-secret"


def test_the_environment_overrides_the_defaults(env):
    env.setenv("RDF_FINGERPRINTER_API_LOCATION", "http://api.test")
    env.setenv("RDF_FINGERPRINTER_API_PORT", "9000")
    env.setenv("RDF_FINGERPRINTER_FUSEKI_LOCATION", "http://jena")
    env.setenv("RDF_FINGERPRINTER_FUSEKI_PORT", "3031")
    env.setenv("RDF_FINGERPRINTER_FUSEKI_USERNAME", "admin")
    env.setenv("RDF_FINGERPRINTER_FUSEKI_PASSWORD", "pw")
    env.setenv("RDF_FINGERPRINTER_REDIS_LOCATION", "redis://cache")
    env.setenv("RDF_FINGERPRINTER_REDIS_PORT", "6380")
    env.setenv("RDF_FINGERPRINTER_FILE_DB", "/data/db")
    env.setenv("RDF_FINGERPRINTER_REPORTS_DB", "/data/reports")
    env.setenv("RDF_FINGERPRINTER_LOG_LEVEL", "debug")
    env.setenv("SHOW_SWAGGER_UI", "false")

    settings = Settings.from_env()

    assert settings.api_url == "http://api.test:9000"
    assert settings.fuseki_url == "http://jena:3031"
    assert (settings.fuseki_user, settings.fuseki_password) == ("admin", "pw")
    assert settings.redis_url == "redis://cache:6380"
    assert (settings.file_db, settings.reports_db) == (Path("/data/db"), Path("/data/reports"))
    assert settings.log_level == "debug"
    assert settings.show_swagger_ui is False


def test_trix_uploads_are_sent_as_application_trix_xml(env):
    mime_types = Settings.from_env().input_mime_types

    assert mime_types["trix"] == "application/trix+xml"
    assert set(mime_types) == {"rdf", "trix", "nq", "nt", "jsonld", "n3", "ttl"}


@pytest.mark.parametrize("variable", [API_KEY, UI_KEY])
def test_a_missing_secret_key_stops_the_start_and_names_the_variable(env, variable):
    env.delenv(variable)

    with pytest.raises(ValueError, match=variable):
        Settings.from_env()


def test_secrets_are_not_shown_in_the_repr(env):
    env.setenv("RDF_FINGERPRINTER_FUSEKI_PASSWORD", "fuseki-pw")

    shown = repr(Settings.from_env())

    for secret in ("api-secret", "ui-secret", "fuseki-pw"):
        assert secret not in shown
