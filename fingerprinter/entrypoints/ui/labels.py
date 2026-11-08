"""Every visible name of the UI: states, formats, messages and sentences (design U-2, DEC-11).

Plain strings only: the UI imports nothing from the service (import contract), so states and
formats are keyed by the values the API sends. Registered as the Jinja global ``labels``.
"""

from dataclasses import dataclass
from typing import Any

MAX_NOTE_LENGTH = 80


@dataclass(frozen=True)
class State:
    label: str
    badge_class: str
    note: str = ""


STATES: dict[str, State] = {
    "queued": State("Queued", "badge-queued", "Waiting for a worker"),
    "running": State("Running…", "badge-running", "Fingerprinting"),
    "completed": State("Done", "badge-done"),
    "completed_with_failures": State("Done with warnings", "badge-warnings"),
    "failed": State("Failed", "badge-failed"),
    "cancelled": State("Cancelled", "badge-cancelled", "Cancelled"),
}


def count(number: int, singular: str, plural: str) -> str:
    """``1 part``, ``3 parts``: the noun agrees with the number."""
    return f"{number} {singular if number == 1 else plural}"


def _summary(reason: str) -> str:
    """The reason up to its first ': ' or '. ', cut to the note's length with an ellipsis."""
    ends = [i for i in (reason.find(": "), reason.find(". ")) if i >= 0]
    text = reason[: min(ends)] if ends else reason
    if len(text) > MAX_NOTE_LENGTH:
        return text[: MAX_NOTE_LENGTH - 1].rstrip() + "…"
    return text


def state_note(
    state: str, *, failures: int = 0, reason: str | None = None, took: str | None = None
) -> str:
    """The line under a status badge; ``took`` is the formatted duration, when it is known."""
    if state == "completed":
        return f"Took {took}" if took else ""
    if state == "completed_with_failures":
        return f"{count(failures, 'part', 'parts')} could not be produced"
    if state == "failed":
        return _summary(reason) if reason else ""
    return STATES[state].note


def source_kind(*, endpoint: bool, graphs: int) -> str:
    """The kind line under a job's source."""
    if not endpoint:
        return "RDF file"
    if graphs == 0:
        return "SPARQL endpoint · all graphs"
    return f"SPARQL endpoint · {count(graphs, 'named graph', 'named graphs')}"


@dataclass(frozen=True)
class Format:
    id: str
    name: str
    description: str


# In display order.
FORMATS: tuple[Format, ...] = (
    Format("html", "Report", "The report page, to keep or share."),
    Format("json", "Profile (JSON)", "Every measurement, for tools and scripts."),
    Format("shacl", "SHACL shapes", "The structure the data has, as SHACL."),
    Format(
        "puml",
        "Class diagram (PlantUML)",
        "The model, and one diagram per vocabulary, as PlantUML text.",
    ),
    Format("svg", "Class diagram (SVG)", "The same diagrams as pictures."),
    Format("pattern", "Pattern schema", "A compact description for people and LLMs."),
    Format("shex", "ShEx schema", "The structure the data has, as ShExC."),
    Format("pitfalls", "Pitfalls (TSV)", "Modelling problems found, one per line."),
    Format("zip", "Download all (.zip)", "Everything above in one archive."),
)


ACTIVE_STATES = frozenset({"queued", "running"})
OUTPUT_STATES = frozenset({"completed", "completed_with_failures"})


@dataclass(frozen=True)
class Filter:
    id: str
    label: str
    states: frozenset[str] | None  # None: every state


DEFAULT_FILTER = "all"
FILTERS: tuple[Filter, ...] = (
    Filter(DEFAULT_FILTER, "All", None),
    Filter("active", "In progress", ACTIVE_STATES),
    Filter("finished", "Finished", OUTPUT_STATES),
    Filter("stopped", "Failed or cancelled", frozenset({"failed", "cancelled"})),
)
FORMAT_NAMES = {f.id: f.name for f in FORMATS}


@dataclass(frozen=True)
class Confirmation:
    title: str
    detail: str
    keep: str
    confirm: str


DELETE_CONFIRMATION = Confirmation(
    "Delete this report?", "This cannot be undone.", "Keep it", "Delete report"
)
CANCEL_CONFIRMATION = Confirmation(
    "Cancel this job?", "The job stops. This cannot be undone.", "Keep it", "Cancel job"
)

OPEN_REPORT = "Open report"
DELETE = "Delete…"
CANCEL_JOB = "Cancel job…"
CHOOSE_A_FILE = "Choose a file to upload."

JOB_STARTED = "Job started."
REPORT_DELETED = "Report deleted."
JOB_CANCELLED = "Job cancelled."

NOT_FOUND_TITLE = "Not found"
FAILED_TITLE = "Something went wrong"
UNREACHABLE = "The service is not reachable. Try again in a moment."
UPDATES_PAUSED = "Status updates paused: the service is not reachable."
SERVER_ERROR = "Something went wrong on the server. Try again."

# The API's problem types (``urn:fingerprinter:<Name>``) and the sentence each one gets.
PROBLEMS: dict[str, str] = {
    "InvalidSource": "Enter an http or https SPARQL endpoint URL, without a user name or password.",
    "UploadTooLarge": "The file is too large (limit {limit} MB).",
    "UnsupportedFileType": "This file type is not supported. Accepted: {accepted}.",
    "QueueUnavailable": "The job queue is unavailable. Try again later.",
    "JobNotFound": "No such job or report.",
    "FormatNotAvailable": "No such job or report.",
    "JobNotCancellable": "This job has already finished.",
    "JobIsActive": "Cancel the job before deleting it.",
    "GraphListingFailed": "Could not list the graphs: {reason}.",
}
PROBLEM_TYPE_PREFIX = "urn:fingerprinter:"


def problem_sentence(problem: dict[str, Any] | None, *, upload_limit_mb: int | None = None) -> str:
    """The sentence for a refused request; the API's ``detail`` only for a type it does not know."""
    problem = problem or {}
    kind = str(problem.get("type", "")).removeprefix(PROBLEM_TYPE_PREFIX)
    if kind in PROBLEMS:
        return PROBLEMS[kind].format(
            limit=upload_limit_mb,
            accepted=", ".join(problem.get("accepted", [])),
            reason=problem.get("detail", ""),
        )
    return str(problem.get("detail") or SERVER_ERROR)
