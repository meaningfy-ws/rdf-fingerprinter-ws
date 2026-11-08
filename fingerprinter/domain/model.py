"""The domain model of a fingerprinting job (design D-1, D-5): pure data, no I/O."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path


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


@dataclass(frozen=True)
class FingerprintOutcome:
    """The files a fingerprinting run wrote, per format, and the measurements that failed."""

    files: Mapping[ReportFormat, tuple[Path, ...]] = field(default_factory=dict)
    failures: tuple[str, ...] = ()

    @property
    def formats(self) -> tuple[ReportFormat, ...]:
        return tuple(fmt for fmt, paths in self.files.items() if paths)
