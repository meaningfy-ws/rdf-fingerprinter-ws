"""``DiagramRenderer`` on a PlantUML server of the stack: the text is posted, an SVG comes back."""

import requests

from fingerprinter.domain.exceptions import DiagramRenderFailed, DiagramServerUnavailable

TIMEOUT_SECONDS = 30
XML_DECLARATION_END = "?>"
# without a charset the server reads the body as Latin-1 and mangles the library's em dashes
TEXT_UTF8 = {"Content-Type": "text/plain; charset=utf-8"}


def _is_svg(body: str) -> bool:
    text = body.strip()
    if text.startswith("<?xml"):
        text = text.partition(XML_DECLARATION_END)[2].lstrip()
    return text.startswith("<svg")


class PlantUmlRenderer:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def render(self, puml_text: str) -> bytes:
        """The SVG of the diagram; the causes name the server's behaviour, never its address."""
        try:
            response = requests.post(
                f"{self.base_url}/svg",
                data=puml_text.encode(),
                headers=TEXT_UTF8,
                timeout=TIMEOUT_SECONDS,
            )
        except requests.Timeout as error:
            raise DiagramServerUnavailable("the PlantUML server did not answer in time") from error
        except requests.RequestException as error:
            raise DiagramServerUnavailable("the PlantUML server is not reachable") from error
        if not response.ok:
            raise DiagramRenderFailed(f"the PlantUML server answered {response.status_code}")
        if not _is_svg(response.text):
            raise DiagramRenderFailed("the PlantUML server did not answer with an SVG")
        return response.content
