"""What the UI raises when the API cannot give it what it asked for."""

from typing import Any


class ApiError(Exception):
    """The API refused a request, or did not answer.

    ``status`` is the HTTP status of the refusal and ``problem`` its RFC 7807 body (``None`` when it
    had none, or was not JSON). An API that gave no answer at all has no status.
    """

    def __init__(self, problem: dict[str, Any] | None = None, status: int | None = None):
        super().__init__(status, problem)
        self.problem = problem
        self.status = status

    @property
    def unreachable(self) -> bool:
        """The API gave no answer: it is down, or too slow."""
        return self.status is None
