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


def test_a_diagram_cannot_make_the_server_fetch_a_url(renderer):
    """The profile of the stack refuses a URL include: no image of what it would have fetched."""
    fetching = "@startuml\n!includeurl http://example.org/x\nclass Fetched\n@enduml\n"

    # observed on jetty-v1.2024.7: the server answers 400 with an error image, whatever the profile
    with pytest.raises(DiagramRenderFailed, match="answered 400"):
        renderer.render(fetching)
