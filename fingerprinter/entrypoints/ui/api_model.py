"""What the API's answers become in the UI: parsed once, with defaults, then used as typed values."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ApiState(StrEnum):
    """The job states the UI knows; a pinned test keeps them equal to the OpenAPI enum."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_FAILURES = "completed_with_failures"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _state(raw: Any) -> ApiState | str:
    """The known state, or the raw text of one this UI does not know (it is shown as it came)."""
    try:
        return ApiState(raw)
    except ValueError:
        return str(raw or "unknown")


@dataclass(frozen=True)
class ApiJob:
    """A job record as ``GET /reports`` lists it."""

    id: str
    created_at: datetime
    state: ApiState | str
    endpoint: str | None = None
    file: str | None = None
    graphs: tuple[str, ...] = ()
    reason: str | None = None
    failures: tuple[str, ...] = ()
    finished_at: datetime | None = None
    files: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def source_name(self) -> str:
        """The endpoint URL or the uploaded file's name."""
        return self.endpoint or self.file or ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApiJob":
        """Only ``id`` and ``created_at`` are required; a missing field takes its default."""
        source = data.get("source") or {}
        finished = data.get("finished_at")
        return cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            state=_state(data.get("state")),
            endpoint=source.get("endpoint"),
            file=source.get("file"),
            graphs=tuple(source.get("graphs") or ()),
            reason=data.get("reason"),
            failures=tuple(data.get("failures") or ()),
            finished_at=datetime.fromisoformat(finished) if finished else None,
            files={fmt: tuple(names) for fmt, names in (data.get("files") or {}).items()},
        )


@dataclass(frozen=True)
class ApiFile:
    """A file the API serves: its type, the name it gave, and its bytes as they arrive."""

    chunks: Iterable[bytes]
    mimetype: str | None = None
    filename: str | None = None
