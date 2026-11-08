"""infra/.env.example: placeholders only, every setting the service reads, none of the library's (D-15)."""

import os
import re
from pathlib import Path

import pytest

from fingerprinter.config import Settings

REPO = Path(__file__).parents[2]
ENV_EXAMPLE = REPO / "infra" / ".env.example"
COMPOSE = REPO / "infra" / "compose.yaml"
DOCKERFILE = REPO / "infra" / "docker" / "Dockerfile"
WORKFLOWS = REPO / ".github" / "workflows"
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
KNOWN_SETTING = (
    "RDF_FINGERPRINTER_FUSEKI_LOCATION"  # read through _service_url, a scan must find it
)


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


def interpolated_in(path: Path) -> set[str]:
    """Every ``${NAME}``, ``${NAME:-default}`` or compose-escaped ``$${NAME}`` the file mentions."""
    return set(re.findall(r"\$\$?\{((?:RDF_FINGERPRINTER_|SHOW_)[A-Z_]+)", path.read_text()))


def set_by_stack_files() -> set[str]:
    """Variables the compose ``environment:`` blocks and the workflows' ``env:`` blocks assign."""
    names: set[str] = set(
        re.findall(r"^\s+((?:RDF_FINGERPRINTER_)[A-Z_]+):", COMPOSE.read_text(), re.M)
    )
    for workflow in WORKFLOWS.glob("*.yml"):
        names |= set(
            re.findall(r"^\s+((?:RDF_FINGERPRINTER_)[A-Z_]+):", workflow.read_text(), re.M)
        )
    return names


@pytest.mark.parametrize("variable", LIBRARY_OPERATIONAL_VARIABLES)
def test_the_library_operational_variables_are_not_set(variable):
    assert variable not in example_settings(), f"{variable} is set in the example"
    assert variable not in set_by_stack_files(), f"{variable} is set in compose or a workflow"


def test_the_config_scan_finds_a_known_setting():
    assert KNOWN_SETTING in settings_read_by_config(), (
        "the scan of config.py found nothing it should"
    )


def test_every_setting_the_service_reads_is_in_the_example():
    missing = settings_read_by_config() - example_settings().keys()
    assert missing == set(), f"not in .env.example: {sorted(missing)}"


@pytest.mark.parametrize("path", [COMPOSE, DOCKERFILE], ids=lambda p: p.name)
def test_every_variable_the_stack_files_interpolate_is_in_the_example(path):
    missing = interpolated_in(path) - example_settings().keys()
    assert interpolated_in(path), f"{path.name}: no variable found, the scan is broken"
    assert missing == set(), (
        f"{path.name} uses variables missing from .env.example: {sorted(missing)}"
    )


@pytest.mark.parametrize(
    "variable",
    [
        "RDF_FINGERPRINTER_API_SECRET_KEY",
        "RDF_FINGERPRINTER_UI_SECRET_KEY",
        "RDF_FINGERPRINTER_FUSEKI_PASSWORD",
    ],
)
def test_secrets_are_placeholders(variable):
    assert example_settings()[variable] == SECRET_PLACEHOLDER, f"{variable} holds a real value"


def test_the_example_is_a_working_configuration(monkeypatch):
    for name in [
        n for n in os.environ if n.startswith("RDF_FINGERPRINTER_") or n == "SHOW_SWAGGER_UI"
    ]:
        monkeypatch.delenv(name)
    for name, value in example_settings().items():
        monkeypatch.setenv(name, value)
    settings = Settings.from_env()
    assert settings.api_url == "http://fingerprinter-api:4020"
