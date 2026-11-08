"""The third-party servers of the test fixtures are those of the stack: images, in-network ports, PlantUML limits (D-13)."""

from pathlib import Path

import pytest
import yaml

from tests import containers

COMPOSE = Path(__file__).parents[2] / "infra" / "compose.yaml"
SANDBOX = "SANDBOX"


def compose_service(name: str) -> dict:
    return yaml.safe_load(COMPOSE.read_text())["services"][name]


@pytest.fixture(scope="module")
def stack_service() -> dict:
    return compose_service("plantuml")


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


@pytest.mark.parametrize(
    ("service", "image", "in_network_port"),
    [
        ("fuseki", containers.FUSEKI_IMAGE, containers.FUSEKI_PORT),
        ("redis", containers.REDIS_IMAGE, containers.REDIS_PORT),
        ("plantuml", containers.PLANTUML_IMAGE, containers.PLANTUML_PORT),
    ],
)
def test_the_stack_runs_the_images_and_ports_of_the_fixtures(service, image, in_network_port):
    definition = compose_service(service)
    published = definition["ports"][0]
    assert definition["image"] == image, f"{service}: compose and tests/containers.py differ"
    assert published.endswith(f":{in_network_port}"), (
        f"{service}: in-network port is not {in_network_port}"
    )
