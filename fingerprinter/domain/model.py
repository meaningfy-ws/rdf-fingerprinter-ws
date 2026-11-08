"""The domain model of a fingerprinting job (design D-1, D-5): pure data, no I/O."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePath
from typing import Any


def file_extension(name: str) -> str:
    """The lower-case extension of a file name, without the dot."""
    return PurePath(name).suffix.lstrip(".").lower()


class ReportFormat(StrEnum):
    HTML = "html"
    JSON = "json"
    SHACL = "shacl"
    PUML = "puml"
    PATTERN = "pattern"
    SHEX = "shex"
    PITFALLS = "pitfalls"
    ZIP = "zip"


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_FAILURES = "completed_with_failures"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_active(self) -> bool:
        return self in (JobState.QUEUED, JobState.RUNNING)


@dataclass(frozen=True)
class Source:
    """What a job fingerprints: a SPARQL endpoint URL or an uploaded file name, never both."""

    endpoint: str | None = None
    file: str | None = None
    graphs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (self.endpoint is None) == (self.file is None):
            raise ValueError("A source is either an endpoint or a file.")


@dataclass(frozen=True)
class JobRecord:
    id: str
    source: Source
    created_at: datetime
    state: JobState
    reason: str | None = None
    failures: tuple[str, ...] = ()
    formats: tuple[ReportFormat, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """The record in the JSON shape of design D-4, shared by ``meta.json`` and the API."""
        where = {"endpoint": self.source.endpoint} if self.source.endpoint else {}
        if self.source.file:
            where = {"file": self.source.file}
        return {
            "id": self.id,
            "source": {**where, "graphs": list(self.source.graphs)},
            "created_at": self.created_at.isoformat(),
            "state": self.state.value,
            "reason": self.reason,
            "failures": list(self.failures),
            "formats": [report_format.value for report_format in self.formats],
        }

    def to_status_dict(self) -> dict[str, Any]:
        """The state of the job, as ``GET /tasks/{task_id}`` answers it."""
        return {
            "task_id": self.id,
            "state": self.state.value,
            "reason": self.reason,
            "failures": list(self.failures),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "JobRecord":
        source = data["source"]
        return cls(
            id=data["id"],
            source=Source(
                endpoint=source.get("endpoint"),
                file=source.get("file"),
                graphs=tuple(source["graphs"]),
            ),
            created_at=datetime.fromisoformat(data["created_at"]),
            state=JobState(data["state"]),
            reason=data["reason"],
            failures=tuple(data["failures"]),
            formats=tuple(ReportFormat(name) for name in data["formats"]),
        )


@dataclass(frozen=True)
class FingerprintOutcome:
    """The files a fingerprinting run wrote, per format, and the measurements that failed."""

    files: Mapping[ReportFormat, tuple[Path, ...]] = field(default_factory=dict)
    failures: tuple[str, ...] = ()

    @property
    def formats(self) -> tuple[ReportFormat, ...]:
        return tuple(fmt for fmt, paths in self.files.items() if paths)
