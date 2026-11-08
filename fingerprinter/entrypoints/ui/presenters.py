"""A job record of the API, as the console words it (design U-2, U-3, U-6)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fingerprinter.entrypoints.ui import labels
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


def source_name(job: dict[str, Any]) -> str:
    """The endpoint URL or the uploaded file's name."""
    source = job["source"]
    return str(source.get("endpoint") or source.get("file") or "")


def present(job: dict[str, Any], now: datetime) -> JobView:
    source = job["source"]
    created = datetime.fromisoformat(job["created_at"])
    finished = datetime.fromisoformat(job["finished_at"]) if job.get("finished_at") else None
    state = job["state"]
    return JobView(
        id=job["id"],
        source=source_name(job),
        kind=labels.source_kind(
            endpoint=bool(source.get("endpoint")), graphs=len(source["graphs"])
        ),
        created_at=created,
        started=when(created, now),
        state=state,
        label=labels.STATES[state].label,
        badge_class=labels.STATES[state].badge_class,
        note=labels.state_note(
            state,
            failures=len(job.get("failures", [])),
            reason=job.get("reason"),
            took=took(created, finished),
        ),
        active=state in labels.ACTIVE_STATES,
        has_outputs=state in labels.OUTPUT_STATES,
    )
