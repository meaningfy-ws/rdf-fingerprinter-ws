"""The messages the UI flashes when the API refuses a request (design, Error matrix)."""

from http import HTTPStatus
from typing import Any

FLASH_ERROR = "error"
FLASH_SUCCESS = "success"
MESSAGES = {
    HTTPStatus.BAD_REQUEST: "Enter an http or https SPARQL endpoint URL.",
    HTTPStatus.NOT_FOUND: "No such job or report.",
    HTTPStatus.CONFLICT: "This job has already finished.",
    HTTPStatus.REQUEST_ENTITY_TOO_LARGE: "The file is too large.",
    HTTPStatus.SERVICE_UNAVAILABLE: "The job queue is unavailable. Try again later.",
}


def error_message(response: Any) -> str:
    """The flash message for an API response that is not a success."""
    if response.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE:
        accepted = ", ".join(response.json().get("accepted", []))
        return f"This file type is not supported. Accepted: {accepted}."
    return MESSAGES.get(
        response.status_code, f"The request failed (status {response.status_code})."
    )
