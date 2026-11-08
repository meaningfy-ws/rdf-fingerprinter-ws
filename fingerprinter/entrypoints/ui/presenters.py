"""A job record of the API, as the console words it (design U-2, U-3, U-6)."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from operator import attrgetter
from typing import NamedTuple

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


SVG_SUFFIX = f".{labels.FormatId.SVG}"
DIAGRAM_PREFIX = "diagram-"
VOCABULARY_SEPARATOR = "--"
PART_SEPARATOR = "~"


class Diagram(NamedTuple):
    file: str
    label: str


class _Parsed(NamedTuple):
    file: str
    slug: str
    vocabulary: str | None
    part: str | None

    @property
    def sort_key(self) -> tuple[bool, str]:
        """Each graph's whole model before the vocabularies, then by file name."""
        return self.vocabulary is not None, self.file


def _parsed(file: str) -> _Parsed:
    stem = file.removesuffix(SVG_SUFFIX).removeprefix(DIAGRAM_PREFIX)
    slug, separator, module = stem.partition(VOCABULARY_SEPARATOR)
    vocabulary, _, part = module.partition(PART_SEPARATOR)
    return _Parsed(file, slug, vocabulary if separator else None, part or None)


def diagram_choices(files: tuple[str, ...]) -> tuple[Diagram, ...]:
    """The picker's diagrams: each graph's whole model first, then the vocabularies (design U-8).

    The library names them ``diagram-<slug>.svg``, ``diagram-<slug>--<vocabulary>.svg`` and, for a
    vocabulary split in parts, ``diagram-<slug>--<vocabulary>~<n>.svg`` (design L-1).
    """
    parsed = sorted((_parsed(file) for file in files), key=attrgetter("sort_key"))
    several = len({item.slug for item in parsed}) > 1
    return tuple(
        Diagram(
            item.file, labels.diagram_label(item.slug, item.vocabulary, item.part, several=several)
        )
        for item in parsed
    )


@dataclass(frozen=True)
class Download:
    format: labels.Format
    name: str | None  # the file's name, when the format holds one file
    count: int  # how many files the download holds


def downloads(files: Mapping[str, tuple[str, ...]]) -> tuple[Download, ...]:
    """One row per format the job holds, in display order, then the zip of everything."""
    rows = [
        Download(fmt, names[0] if len(names) == 1 else None, len(names))
        for fmt in labels.FORMATS
        if (names := files.get(fmt.id, ())) and fmt.id != labels.FormatId.ZIP
    ]
    everything = sum(len(names) for names in files.values())
    if everything:
        rows.append(Download(labels.ZIP_FORMAT, None, everything))
    return tuple(rows)
