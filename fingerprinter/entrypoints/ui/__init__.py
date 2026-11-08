"""The UI: a Flask 3 app that is a client of the API over HTTP and nothing else (design D-9)."""

from flask import Flask

from fingerprinter.entrypoints.ui import views
from fingerprinter.entrypoints.ui.api_wrapper import ApiClient


def create_app(api_base_url: str, secret_key: str) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = secret_key
    app.extensions["api"] = ApiClient(api_base_url)
    views.register(app)
    return app
