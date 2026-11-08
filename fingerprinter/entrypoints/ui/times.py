"""How the console words a time and a duration (design U-6)."""

from dataclasses import dataclass
from datetime import UTC, datetime, tzinfo

SECONDS_PER_MINUTE = 60
JUST_NOW = "just now"


@dataclass(frozen=True)
class Shown:
    """A time ready for ``<time datetime="{iso}" title="{title}">{text}</time>``."""

    text: str
    iso: str
    title: str


def _date(moment: datetime) -> str:
    return f"{moment.day} {moment:%b %Y}"


def when(moment: datetime, now: datetime | None = None, *, tz: tzinfo | None = None) -> Shown:
    """``moment`` in words, in ``tz`` (the server's zone when ``None``) as seen at ``now``."""
    now = now or datetime.now(UTC)
    local, here = moment.astimezone(tz), now.astimezone(tz)
    minutes = int((now - moment).total_seconds() // SECONDS_PER_MINUTE)
    clock = f"{local:%H:%M}"
    if minutes < 1:  # also a time in the future: the clocks disagree
        text = JUST_NOW
    elif minutes < SECONDS_PER_MINUTE:
        text = f"{minutes} min ago"
    elif local.date() == here.date():
        text = f"Today, {clock}"
    elif (here.date() - local.date()).days == 1:
        text = f"Yesterday, {clock}"
    else:
        text = f"{_date(local)}, {clock}"
    return Shown(text, moment.isoformat(), f"{_date(local)}, {clock}")


def took(created: datetime, finished: datetime | None) -> str | None:
    """The duration from ``created`` to ``finished``; ``None`` while the finish time is unknown."""
    if finished is None:
        return None
    seconds = max((finished - created).total_seconds(), 0)
    if round(seconds, 1) < SECONDS_PER_MINUTE:
        return f"{seconds:.1f} s"
    minutes, rest = divmod(round(seconds), SECONDS_PER_MINUTE)
    return f"{minutes} min {rest} s"
