"""The API: a Connexion 3 app over the OpenAPI contract, calling the services (design D-4, D-8)."""

from collections.abc import Callable

from connexion import FlaskApp
from connexion.lifecycle import ConnexionRequest, ConnexionResponse
from connexion.options import SwaggerUIOptions
from connexion.problem import problem

from fingerprinter.domain.exceptions import (
    FormatNotAvailable,
    InvalidSource,
    JobNotCancellable,
    JobNotFound,
    QueueUnavailable,
    UnsupportedFileType,
)
from fingerprinter.services.ports import Services

# Each domain exception and the status its problem response carries (design D-4, Error matrix).
PROBLEM_STATUS: dict[type[Exception], int] = {
    InvalidSource: 400,
    UnsupportedFileType: 415,
    JobNotFound: 404,
    FormatNotAvailable: 404,
    JobNotCancellable: 409,
    QueueUnavailable: 503,
}


def _problem_handler(
    exception: type[Exception], status: int
) -> Callable[[ConnexionRequest, Exception], ConnexionResponse]:
    def handle(_request: ConnexionRequest, error: Exception) -> ConnexionResponse:
        accepted = error.accepted if isinstance(error, UnsupportedFileType) else None
        return problem(
            status=status,
            title=exception.__name__,
            detail=str(error),
            type=f"urn:fingerprinter:{exception.__name__}",
            ext={"accepted": list(accepted)} if accepted else None,
        )

    return handle


def create_app(services: Services, *, swagger_ui: bool = True) -> FlaskApp:
    app = FlaskApp(
        __name__,
        specification_dir="openapi",
        swagger_ui_options=SwaggerUIOptions(swagger_ui=swagger_ui),
    )
    # Flask answers an unhandled exception itself unless it propagates to the handlers below.
    app.app.config["PROPAGATE_EXCEPTIONS"] = True
    app.app.extensions["fingerprinter"] = services
    app.add_api("fingerprinter.yml")
    for exception, status in PROBLEM_STATUS.items():
        app.add_error_handler(exception, _problem_handler(exception, status))
    return app
