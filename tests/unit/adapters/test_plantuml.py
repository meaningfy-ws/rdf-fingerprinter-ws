"""The PlantUML adapter's SVG rule (design U-9) and its errors, which name the cause, never the URL."""

import pytest
import requests

from fingerprinter.adapters.plantuml import PlantUmlRenderer
from fingerprinter.domain.exceptions import DiagramRenderFailed, DiagramServerUnavailable

INTERNAL_URL = "http://plantuml-internal:8080"
PUML = "@startuml\nclass Ä\n@enduml\n"
SVG = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'


@pytest.fixture
def renderer() -> PlantUmlRenderer:
    return PlantUmlRenderer(INTERNAL_URL)


def answer(monkeypatch, status: int = 200, body: str | bytes = SVG) -> list:
    """Make ``requests.post`` answer; the returned list collects the calls made."""
    calls = []
    response = requests.Response()
    response.status_code = status
    response._content = body.encode() if isinstance(body, str) else body

    def post(*args, **kwargs):
        calls.append((args, kwargs))
        return response

    monkeypatch.setattr(requests, "post", post)
    return calls


def test_the_text_is_posted_unchanged_to_the_svg_endpoint_with_a_timeout(renderer, monkeypatch):
    calls = answer(monkeypatch)

    renderer.render(PUML)

    (((url,), kwargs),) = calls
    assert url == f"{INTERNAL_URL}/svg"
    assert kwargs["data"] == PUML.encode()
    assert kwargs["timeout"] == 30


@pytest.mark.parametrize(
    "body",
    [
        SVG,
        f"\n  {SVG}\n",
        f'<?xml version="1.0" encoding="UTF-8"?>{SVG}',
        f'<?xml version="1.0"?>\n{SVG}',
    ],
)
def test_an_svg_answer_is_returned_as_given(renderer, monkeypatch, body):
    answer(monkeypatch, body=body)

    assert renderer.render(PUML) == body.encode()


@pytest.mark.parametrize(
    "body", ["<html></html>", "", "Syntax Error?", '<?xml version="1.0"?><html/>']
)
def test_a_2xx_answer_that_is_not_svg_is_an_error(renderer, monkeypatch, body):
    answer(monkeypatch, body=body)

    with pytest.raises(DiagramRenderFailed, match="did not answer with an SVG"):
        renderer.render(PUML)


def test_a_refused_diagram_is_an_error_naming_the_status(renderer, monkeypatch):
    answer(monkeypatch, status=400)  # PlantUML answers a syntax error with 400 and an SVG

    with pytest.raises(DiagramRenderFailed, match="answered 400"):
        renderer.render(PUML)


@pytest.mark.parametrize(
    ("error", "cause"),
    [
        (requests.ConnectionError(INTERNAL_URL), "is not reachable"),
        (requests.Timeout(INTERNAL_URL), "did not answer in time"),
    ],
)
def test_an_unreachable_or_slow_server_is_an_error_without_the_url(
    renderer, monkeypatch, error, cause
):
    def post(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(requests, "post", post)

    with pytest.raises(DiagramServerUnavailable, match=cause) as raised:
        renderer.render(PUML)

    assert INTERNAL_URL not in str(raised.value)
