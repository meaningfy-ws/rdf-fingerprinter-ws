"""The PlantUML adapter against a real PlantUML server (class-diagram: A diagram is rendered)."""

import pytest

from fingerprinter.adapters.plantuml import PlantUmlRenderer
from fingerprinter.domain.exceptions import DiagramRenderFailed
from tests.containers import PlantUmlServer

SMALL_DIAGRAM = "@startuml\nclass Country\nclass Continent\nContinent --> Country\n@enduml\n"


@pytest.fixture
def renderer(plantuml: PlantUmlServer) -> PlantUmlRenderer:
    return PlantUmlRenderer(plantuml.url)


def test_a_small_diagram_is_drawn_as_svg(renderer):
    svg = renderer.render(SMALL_DIAGRAM)

    assert svg.lstrip().startswith((b"<svg", b"<?xml"))
    assert b"Country" in svg


def test_a_diagram_the_server_refuses_is_an_error(renderer):
    with pytest.raises(DiagramRenderFailed):
        renderer.render("this is not a diagram")


def test_a_server_that_is_not_there_is_an_error():
    with pytest.raises(DiagramRenderFailed, match="not reachable"):
        PlantUmlRenderer("http://127.0.0.1:1").render(SMALL_DIAGRAM)
