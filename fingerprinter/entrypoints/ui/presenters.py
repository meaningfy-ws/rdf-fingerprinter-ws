"""A job record of the API, as the console words it (design U-2, U-3, U-6)."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from fingerprinter.entrypoints.ui import labels
from fingerprinter.entrypoints.ui.api_model import ApiJob
from fingerprinter.entrypoints.ui.times import Shown, took, when


@dataclass(frozen=True)
class JobView:
    id: str
    source: str
    kind: str
    created_at: datetime
    started: Shown
    state: str
    label: str
    badge_class: str
    note: str
    active: bool
    has_outputs: bool
    short_id: str
    took: str | None
    reason: str | None
    failures: tuple[str, ...]
    files: Mapping[str, tuple[str, ...]]


SHORT_ID_LENGTH = 8


def present(job: ApiJob, now: datetime) -> JobView:
    # a state this UI does not know shows as it came, with a neutral badge
    known = labels.STATES.get(job.state) or labels.State(str(job.state), labels.UNKNOWN_BADGE)
    duration = took(job.created_at, job.finished_at)
    return JobView(
        id=job.id,
        source=job.source_name,
        kind=labels.source_kind(endpoint=bool(job.endpoint), graphs=len(job.graphs)),
        created_at=job.created_at,
        started=when(job.created_at, now),
        state=job.state,
        label=known.label,
        badge_class=known.badge_class,
        note=labels.state_note(
            job.state,
            failures=len(job.failures),
            reason=job.reason,
            took=duration,
        ),
        active=job.state in labels.ACTIVE_STATES,
        has_outputs=job.state in labels.OUTPUT_STATES,
        short_id=job.id[:SHORT_ID_LENGTH],
        took=duration,
        reason=job.reason,
        failures=job.failures,
        files=job.files,
    )


SVG_SUFFIX = ".svg"
DIAGRAM_PREFIX = "diagram-"
VOCABULARY_SEPARATOR = "--"


@dataclass(frozen=True)
class Diagram:
    file: str
    label: str


def diagram_choices(files: tuple[str, ...]) -> tuple[Diagram, ...]:
    """The picker's diagrams: each graph's whole model first, then the vocabularies (design U-8).

    The library names them ``diagram-<slug>.svg`` and ``diagram-<slug>--<vocabulary>.svg``.
    """
    parsed = []
    for file in files:
        stem = file.removesuffix(SVG_SUFFIX).removeprefix(DIAGRAM_PREFIX)
        slug, _, vocabulary = stem.partition(VOCABULARY_SEPARATOR)
        parsed.append((bool(vocabulary), file, slug, vocabulary or None))
    several = len({slug for *_, slug, _ in parsed}) > 1
    return tuple(
        Diagram(file, labels.diagram_label(slug, vocabulary, several=several))
        for _, file, slug, vocabulary in sorted(parsed)
    )


@dataclass(frozen=True)
class Download:
    format: labels.Format
    file: str  # the file's name, or how many files the zip holds


def downloads(files: Mapping[str, tuple[str, ...]]) -> tuple[Download, ...]:
    """One row per format the job holds, in display order, then the zip of everything."""
    rows = [
        Download(fmt, names[0] if len(names) == 1 else labels.zip_of(len(names)))
        for fmt in labels.FORMATS
        if (names := files.get(fmt.id, ())) and fmt.id != labels.FormatId.ZIP
    ]
    everything = sum(len(names) for names in files.values())
    if everything:
        rows.append(Download(labels.ZIP_FORMAT, labels.zip_of(everything)))
    return tuple(rows)
