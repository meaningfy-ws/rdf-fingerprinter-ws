"""Every visible name of the UI: states, formats, messages and sentences (design U-2, DEC-11).

The UI imports nothing from the service (import contract), so states and formats are keyed by
UI-local enums holding the values the API sends. Registered as the Jinja global ``labels``.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from fingerprinter.entrypoints.ui.api_model import ApiState

MAX_NOTE_LENGTH = 80


@dataclass(frozen=True)
class State:
    label: str
    badge_class: str
    note: str = ""


STATES: dict[str, State] = {
    ApiState.QUEUED: State("Queued", "badge-queued", "Waiting for a worker"),
    ApiState.RUNNING: State("Running…", "badge-running", "Fingerprinting"),
    ApiState.COMPLETED: State("Done", "badge-done"),
    ApiState.COMPLETED_WITH_FAILURES: State("Done with warnings", "badge-warnings"),
    ApiState.FAILED: State("Failed", "badge-failed"),
    ApiState.CANCELLED: State("Cancelled", "badge-cancelled", "Cancelled"),
}
UNKNOWN_BADGE = "badge-unknown"  # a state this UI does not know: its raw text, a neutral badge


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
    if state == ApiState.COMPLETED:
        return f"Took {took}" if took else ""
    if state == ApiState.COMPLETED_WITH_FAILURES:
        return f"{count(failures, 'part', 'parts')} could not be produced"
    if state == ApiState.FAILED:
        return _summary(reason) if reason else ""
    return STATES[state].note if state in STATES else ""


def source_kind(*, endpoint: bool, graphs: int) -> str:
    """The kind line under a job's source."""
    if not endpoint:
        return "RDF file"
    if graphs == 0:
        return "SPARQL endpoint · all graphs"
    return f"SPARQL endpoint · {count(graphs, 'named graph', 'named graphs')}"


class FormatId(StrEnum):
    HTML = "html"
    JSON = "json"
    SHACL = "shacl"
    PUML = "puml"
    SVG = "svg"
    PATTERN = "pattern"
    SHEX = "shex"
    PITFALLS = "pitfalls"
    ZIP = "zip"


@dataclass(frozen=True)
class Format:
    id: FormatId
    name: str
    description: str


# In display order.
FORMATS: tuple[Format, ...] = (
    Format(FormatId.HTML, "Report", "The report page, to keep or share."),
    Format(FormatId.JSON, "Profile (JSON)", "Every measurement, for tools and scripts."),
    Format(FormatId.SHACL, "SHACL shapes", "The structure the data has, as SHACL."),
    Format(
        FormatId.PUML,
        "Class diagram (PlantUML)",
        "The model, and one diagram per vocabulary, as PlantUML text.",
    ),
    Format(FormatId.SVG, "Class diagram (SVG)", "The same diagrams as pictures."),
    Format(FormatId.PATTERN, "Pattern schema", "A compact description for people and LLMs."),
    Format(FormatId.SHEX, "ShEx schema", "The structure the data has, as ShExC."),
    Format(FormatId.PITFALLS, "Pitfalls (TSV)", "Modelling problems found, one per line."),
    Format(FormatId.ZIP, "Download all (.zip)", "Everything above in one archive."),
)

ZIP_FORMAT = next(f for f in FORMATS if f.id == FormatId.ZIP)

ACTIVE_STATES = frozenset({ApiState.QUEUED, ApiState.RUNNING})
OUTPUT_STATES = frozenset({ApiState.COMPLETED, ApiState.COMPLETED_WITH_FAILURES})


@dataclass(frozen=True)
class Filter:
    id: str
    label: str
    states: frozenset[ApiState] | None  # None: every state


DEFAULT_FILTER = "all"
FILTERS: tuple[Filter, ...] = (
    Filter(DEFAULT_FILTER, "All", None),
    Filter("active", "In progress", ACTIVE_STATES),
    Filter("finished", "Finished", OUTPUT_STATES),
    Filter("stopped", "Failed or cancelled", frozenset({ApiState.FAILED, ApiState.CANCELLED})),
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


class JobTab(StrEnum):
    """What the Job page shows: the value of ``?tab=``; a missing or unknown one is the report."""

    REPORT = "report"
    DIAGRAM = "diagram"
    DOWNLOADS = "downloads"


JOB_TAB_NAMES = {
    JobTab.REPORT: "Report",
    JobTab.DIAGRAM: "Class diagram",
    JobTab.DOWNLOADS: "Downloads",
}
WHOLE_MODEL = "Whole model"
DIAGRAM_PICKER = "Diagram"
SHOW = "Show"
NO_DIAGRAM = "No diagram is available."
UNKNOWN_DIAGRAM = "That diagram does not exist."
OPEN_IN_NEW_TAB = "Open in a new tab"
DOWNLOAD = "Download"
DOWNLOAD_SVG = "Download SVG"
WHY_IT_FAILED = "Why it failed"


def warnings_title(failures: int) -> str:
    return f"Some parts could not be produced ({failures})"


def diagram_label(slug: str, vocabulary: str | None, *, several: bool) -> str:
    """The picker's name for a diagram; the graph is named only when the job has several."""
    text = f"Vocabulary: {vocabulary}" if vocabulary else WHOLE_MODEL
    return f"{text} — {slug}" if several else text


def zip_of(files: int) -> str:
    return f"{count(files, 'file', 'files')} (.zip)"


OPEN_REPORT = "Open report"
DELETE = "Delete…"
CANCEL_JOB = "Cancel job…"
CHOOSE_A_FILE = "Choose a file to upload."
NEW_JOB = "New job"
START_FINGERPRINTING = "Start fingerprinting"
CANCEL = "Cancel"
BACK_TO_JOBS = "Back to Jobs"
SHOW_ALL = "Show all"
NO_JOBS_YET = "No jobs yet."
NO_JOBS_HERE = "No jobs here."
START_ONE_FROM_A = "Start one from a"
OR_AN = "or an"
SPARQL_ENDPOINT = "SPARQL endpoint"
DROP_A_FILE = "Drop a file here, or choose one."


class Tab(StrEnum):
    """Where the data of a new job comes from: the value of ``?from=`` on the New job page."""

    ENDPOINT = "endpoint"
    FILE = "file"


TAB_NAMES = {Tab.ENDPOINT: "From an endpoint", Tab.FILE: "From a file"}

ENDPOINT_URL_LABEL = "SPARQL endpoint URL"
ENDPOINT_URL_HELP = "The query endpoint, for example http://localhost:3030/dataset/sparql."
GRAPHS_LABEL = "Named graphs (optional)"
GRAPHS_HELP = (
    "One graph IRI per line, or separated by spaces. "
    "Leave empty to profile every graph, including the default graph."
)
FILE_LABEL = "RDF file"

JOB_STARTED = "Job started."
REPORT_DELETED = "Report deleted."
JOB_CANCELLED = "Job cancelled."

NOT_FOUND_TITLE = "Not found"
FAILED_TITLE = "Something went wrong"
UNREACHABLE = "The service is not reachable. Try again in a moment."
UPDATES_PAUSED = "Status updates paused: the service is not reachable."
SERVER_ERROR = "Something went wrong on the server. Try again."
FORM_EXPIRED = "This form expired. Please try again."

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
        )
    return str(problem.get("detail") or SERVER_ERROR)
