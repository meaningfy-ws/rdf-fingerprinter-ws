"""infra/.env.example: placeholders only, every setting the service reads, none of the library's (D-15)."""

import os
import re
from pathlib import Path

import pytest

from fingerprinter.config import Settings

REPO = Path(__file__).parents[2]
ENV_EXAMPLE = REPO / "infra" / ".env.example"
CONFIG = REPO / "fingerprinter" / "config.py"

LIBRARY_OPERATIONAL_VARIABLES = tuple(
    f"RDF_FINGERPRINTER_{name}"
    for name in (
        "PROFILE_FILE",
        "RETRY_BACKOFF_SECONDS",
        "TIMEOUT_MARKERS",
        "ERROR_EXCERPT_LENGTH",
        "SHAPES_NAMESPACE",
        "DEFAULT_GRAPH_LABEL",
        "PREFIXES_FILE",
        "PREFIX_LOOKUP",
    )
)
SECRET_PLACEHOLDER = "change-me"


def example_settings() -> dict[str, str]:
    lines = (line.strip() for line in ENV_EXAMPLE.read_text().splitlines())
    return dict(line.split("=", 1) for line in lines if line and not line.startswith("#"))


def settings_read_by_config() -> set[str]:
    """Every variable ``Settings.from_env`` reads: the literal names, and the location and port of each service."""
    source = CONFIG.read_text()
    literal = set(re.findall(r'"((?:RDF_FINGERPRINTER_|SHOW_)[A-Z_]+)"', source))
    services = re.findall(r'_service_url\("([A-Z]+)"', source)
    return literal | {
        f"RDF_FINGERPRINTER_{s}_{part}" for s in services for part in ("LOCATION", "PORT")
    }


@pytest.mark.parametrize("variable", LIBRARY_OPERATIONAL_VARIABLES)
def test_the_library_operational_variables_are_not_set(variable):
    assert variable not in example_settings()


def test_every_setting_the_service_reads_is_in_the_example():
    assert settings_read_by_config() - example_settings().keys() == set()


@pytest.mark.parametrize(
    "variable", ["RDF_FINGERPRINTER_API_SECRET_KEY", "RDF_FINGERPRINTER_UI_SECRET_KEY"]
)
def test_secrets_are_placeholders(variable):
    assert example_settings()[variable] == SECRET_PLACEHOLDER


def test_the_example_is_a_working_configuration(monkeypatch):
    for name in [
        n for n in os.environ if n.startswith("RDF_FINGERPRINTER_") or n == "SHOW_SWAGGER_UI"
    ]:
        monkeypatch.delenv(name)
    for name, value in example_settings().items():
        monkeypatch.setenv(name, value)
    Settings.from_env()
