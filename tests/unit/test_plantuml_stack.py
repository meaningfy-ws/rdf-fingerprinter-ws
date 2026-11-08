"""The PlantUML server of the test fixture is the one of the stack: image, size limit, security profile."""

from pathlib import Path

import pytest
import yaml

from tests import containers

COMPOSE = Path(__file__).parents[2] / "docker" / "docker-compose.yml"
SANDBOX = "SANDBOX"


@pytest.fixture(scope="module")
def stack_service() -> dict:
    return yaml.safe_load(COMPOSE.read_text())["services"]["plantuml"]


def environment(service: dict) -> dict[str, str]:
    return dict(entry.split("=", 1) for entry in service["environment"])


def test_the_fixture_runs_the_image_of_the_stack(stack_service):
    assert stack_service["image"] == containers.PLANTUML_IMAGE


def test_the_fixture_has_the_size_limit_of_the_stack(stack_service):
    assert environment(stack_service)["PLANTUML_LIMIT_SIZE"] == containers.PLANTUML_LIMIT_SIZE


def test_no_diagram_can_make_the_server_fetch_a_url(stack_service):
    """A diagram's text comes from profiled data: the sandbox profile refuses every URL."""
    assert environment(stack_service)["PLANTUML_SECURITY_PROFILE"] == SANDBOX
    assert containers.PLANTUML_SECURITY_PROFILE == SANDBOX
