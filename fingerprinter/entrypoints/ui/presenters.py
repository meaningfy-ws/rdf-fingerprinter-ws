"""A job record of the API, as the console words it (design U-2, U-3, U-6)."""

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


def present(job: ApiJob, now: datetime) -> JobView:
    # a state this UI does not know shows as it came, with a neutral badge
    known = labels.STATES.get(job.state) or labels.State(str(job.state), labels.UNKNOWN_BADGE)
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
            took=took(job.created_at, job.finished_at),
        ),
        active=job.state in labels.ACTIVE_STATES,
        has_outputs=job.state in labels.OUTPUT_STATES,
    )
