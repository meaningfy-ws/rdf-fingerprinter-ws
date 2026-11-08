"""The UI: a Flask 3 app that is a client of the API over HTTP and nothing else (design D-9)."""

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from fingerprinter.entrypoints.ui import labels, views
from fingerprinter.entrypoints.ui.api_client import ApiClient


def create_app(
    api_base_url: str,
    secret_key: str,
    *,
    accepted_extensions: tuple[str, ...],
    max_upload_bytes: int,
    secure_cookies: bool = False,
) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = secret_key
    app.config[views.CONFIG_ACCEPTED_EXTENSIONS] = accepted_extensions
    app.config[views.CONFIG_MAX_UPLOAD_BYTES] = max_upload_bytes
    # room for the form around the file; a larger request never reaches the API (design U-7)
    app.config["MAX_CONTENT_LENGTH"] = max_upload_bytes + views.BYTES_PER_MB
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = secure_cookies
    CSRFProtect(app)
    app.jinja_env.globals.update(
        FLASH_ERROR=views.FLASH_ERROR, FLASH_SUCCESS=views.FLASH_SUCCESS, labels=labels
    )
    app.extensions[views.API_EXTENSION] = ApiClient(api_base_url)
    views.register(app)
    return app
