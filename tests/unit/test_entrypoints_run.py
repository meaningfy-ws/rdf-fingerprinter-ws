"""The gunicorn targets the images start: the API's ASGI app and the UI's WSGI app."""

import logging

from connexion import FlaskApp
from flask import Flask


def test_the_api_target_is_the_connexion_app():
    from fingerprinter.entrypoints.api.run import connexion_app

    assert isinstance(connexion_app, FlaskApp)


def test_the_ui_target_is_the_flask_app():
    from fingerprinter.entrypoints.ui.run import app

    assert isinstance(app, Flask)


def test_the_service_logs_at_the_configured_level(monkeypatch):
    from fingerprinter.logging_setup import configure_logging

    configure_logging("debug")

    assert logging.getLogger("fingerprinter").getEffectiveLevel() == logging.DEBUG
