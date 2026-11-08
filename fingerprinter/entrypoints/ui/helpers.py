"""The messages the UI flashes when the API refuses a request (design, Error matrix)."""

from typing import Any

UNSUPPORTED_FILE_TYPE = 415
MESSAGES = {
    400: "Enter an http or https SPARQL endpoint URL.",
    404: "No such job or report.",
    409: "This job has already finished.",
    503: "The job queue is unavailable. Try again later.",
}


def error_message(response: Any) -> str:
    """The flash message for an API response that is not a success."""
    if response.status_code == UNSUPPORTED_FILE_TYPE:
        accepted = ", ".join(response.json().get("accepted", []))
        return f"This file type is not supported. Accepted: {accepted}."
    return MESSAGES.get(
        response.status_code, f"The request failed (status {response.status_code})."
    )
