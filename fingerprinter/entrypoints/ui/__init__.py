"""The UI: a Flask 3 app that is a client of the API over HTTP and nothing else (design D-9)."""

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from fingerprinter.entrypoints.ui import labels, views
from fingerprinter.entrypoints.ui.api_wrapper import ApiClient
from fingerprinter.entrypoints.ui.helpers import FLASH_ERROR, FLASH_SUCCESS

EXTRA_FORM_BYTES = 1024 * 1024


def create_app(
    api_base_url: str,
    secret_key: str,
    *,
    accepted_extensions: tuple[str, ...],
    max_upload_bytes: int,
) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = secret_key
    app.config["ACCEPTED_EXTENSIONS"] = accepted_extensions
    app.config["MAX_UPLOAD_BYTES"] = max_upload_bytes
    # room for the form around the file; a larger request never reaches the API (design U-7)
    app.config["MAX_CONTENT_LENGTH"] = max_upload_bytes + EXTRA_FORM_BYTES
    CSRFProtect(app)
    app.jinja_env.globals.update(
        FLASH_ERROR=FLASH_ERROR, FLASH_SUCCESS=FLASH_SUCCESS, labels=labels
    )
    app.extensions["api"] = ApiClient(api_base_url)
    views.register(app)
    return app
