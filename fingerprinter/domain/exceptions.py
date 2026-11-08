"""Domain errors; the API maps each to a problem response (design D-4, Error matrix)."""

from collections.abc import Iterable

from fingerprinter.domain.model import JobState, ReportFormat


class InvalidSource(Exception):
    """The endpoint URL is not an http or https URL, or carries user info (400)."""


class GraphListingFailed(Exception):
    """The endpoint's named graphs could not be listed; the message is the plain reason (502)."""


class UnsupportedFileType(Exception):
    """The uploaded file's extension is not accepted (415)."""

    def __init__(self, filename: str, accepted: Iterable[str]):
        self.accepted = tuple(sorted(accepted))
        super().__init__(f'"{filename}" is not supported. Accepted: {", ".join(self.accepted)}.')


class UploadTooLarge(Exception):
    """The uploaded file is larger than the service accepts (413)."""

    def __init__(self, filename: str, max_bytes: int):
        super().__init__(f'"{filename}" is larger than the {max_bytes}-byte upload limit.')


class DiagramRenderFailed(Exception):
    """A class diagram could not be drawn; the message is the cause. Never an API problem."""


class DiagramServerUnavailable(DiagramRenderFailed):
    """The PlantUML server is unreachable or too slow: no other diagram of the job is tried."""


class JobNotFound(Exception):
    """No job or report has this id (404)."""

    def __init__(self, job_id: str):
        super().__init__(f'No job or report "{job_id}".')


class FormatNotAvailable(Exception):
    """The report holds no file of this format (404)."""

    def __init__(self, job_id: str, report_format: ReportFormat):
        super().__init__(f'Report "{job_id}" has no {report_format} output.')


class JobNotCancellable(Exception):
    """The job is not queued or running (409)."""

    def __init__(self, job_id: str, state: JobState):
        super().__init__(f'Job "{job_id}" is {state} and cannot be cancelled.')


class JobIsActive(Exception):
    """The job is queued or running and cannot be deleted (409)."""

    def __init__(self, job_id: str, state: JobState):
        super().__init__(f'Job "{job_id}" is {state}: cancel it before deleting it.')


class QueueUnavailable(Exception):
    """The job queue refused the job (503)."""
