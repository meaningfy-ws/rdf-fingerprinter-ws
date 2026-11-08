"""The service's settings, read once from the environment by ``bootstrap`` (design D-7).

Nothing else imports this module: entrypoints, services and adapters receive the values they need.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

INPUT_MIME_TYPES: Mapping[str, str] = {
    "rdf": "application/rdf+xml",
    "trix": "application/trix+xml",
    "nq": "application/n-quads",
    "nt": "application/n-triples",
    "jsonld": "application/ld+json",
    "n3": "text/n3",
    "ttl": "text/turtle",
}

# The media type of each file extension the downloads carry: the library's outputs, so that the type
# does not depend on the Python version's own table.
OUTPUT_MIME_TYPES: Mapping[str, str] = {
    "html": "text/html",
    "json": "application/json",
    "ttl": "text/turtle",
    "shex": "text/shex",
    "tsv": "text/tab-separated-values",
    "md": "text/markdown",
    "csv": "text/csv",
    "puml": "text/plain",
    "zip": "application/zip",
}

BYTES_PER_MB = 1024 * 1024


def strtobool(value: str) -> bool:
    """The truth value of a setting, as distutils.util.strtobool (removed in Python 3.12) gave it."""
    normalised = value.strip().lower()
    if normalised in ("1", "true", "yes", "on", "y", "t"):
        return True
    if normalised in ("0", "false", "no", "off", "n", "f"):
        return False
    raise ValueError(f"invalid truth value {value!r}")


def _service_url(name: str, default_location: str, default_port: int) -> str:
    location = os.environ.get(f"RDF_FINGERPRINTER_{name}_LOCATION", default_location)
    return f"{location}:{os.environ.get(f'RDF_FINGERPRINTER_{name}_PORT', default_port)}"


def _required(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError:
        raise ValueError(f"{name} must be set: it has no default.") from None


@dataclass(frozen=True)
class Settings:
    api_url: str
    fuseki_url: str
    redis_url: str = field(repr=False)
    api_secret_key: str = field(repr=False)
    ui_secret_key: str = field(repr=False)
    fuseki_user: str
    fuseki_password: str = field(repr=False)
    file_db: Path
    reports_db: Path
    max_upload_bytes: int
    show_swagger_ui: bool
    log_level: str
    ui_secure_cookies: bool
    input_mime_types: Mapping[str, str] = field(default_factory=lambda: INPUT_MIME_TYPES)
    output_mime_types: Mapping[str, str] = field(default_factory=lambda: OUTPUT_MIME_TYPES)

    @classmethod
    def from_env(cls) -> "Settings":
        root = Path(__file__).parents[1]
        env = os.environ
        return cls(
            api_url=_service_url("API", "http://fingerprinter-api", 4020),
            fuseki_url=_service_url("FUSEKI", "http://fuseki", 3030),
            redis_url=_service_url("REDIS", "redis://redis", 6379),
            api_secret_key=_required("RDF_FINGERPRINTER_API_SECRET_KEY"),
            ui_secret_key=_required("RDF_FINGERPRINTER_UI_SECRET_KEY"),
            fuseki_user=env.get("RDF_FINGERPRINTER_FUSEKI_USERNAME", ""),
            fuseki_password=env.get("RDF_FINGERPRINTER_FUSEKI_PASSWORD", ""),
            file_db=Path(env.get("RDF_FINGERPRINTER_FILE_DB", root / "db")),
            reports_db=Path(env.get("RDF_FINGERPRINTER_REPORTS_DB", root / "reports")),
            max_upload_bytes=int(env.get("RDF_FINGERPRINTER_MAX_UPLOAD_MB", 512)) * BYTES_PER_MB,
            show_swagger_ui=strtobool(env.get("SHOW_SWAGGER_UI", "true")),
            log_level=env.get("RDF_FINGERPRINTER_LOG_LEVEL", "info"),
            ui_secure_cookies=strtobool(env.get("RDF_FINGERPRINTER_UI_SECURE_COOKIES", "false")),
        )
