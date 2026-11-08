"""How the console words a time and a duration (design U-6): one test per threshold."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from fingerprinter.entrypoints.ui.times import took, when

NOW = datetime(2026, 11, 8, 14, 30, tzinfo=UTC)
PLUS_TWO = timezone(timedelta(hours=2))


def ago(**delta: float) -> datetime:
    return NOW - timedelta(**delta)


@pytest.mark.parametrize(
    ("moment", "text"),
    [
        (ago(seconds=0), "just now"),
        (ago(seconds=59), "just now"),
        (NOW + timedelta(minutes=5), "just now"),  # the clocks disagree: never "in the future"
        (ago(minutes=1), "1 min ago"),
        (ago(minutes=1, seconds=59), "1 min ago"),  # whole minutes, rounded down
        (ago(minutes=59, seconds=59), "59 min ago"),
        (ago(minutes=60), "Today, 13:30"),
        (datetime(2026, 11, 8, 0, 5, tzinfo=UTC), "Today, 00:05"),
        (datetime(2026, 11, 7, 23, 59, tzinfo=UTC), "Yesterday, 23:59"),
        (datetime(2026, 11, 7, 0, 0, tzinfo=UTC), "Yesterday, 00:00"),
        (datetime(2026, 11, 6, 23, 59, tzinfo=UTC), "6 Nov 2026, 23:59"),
        (datetime(2025, 1, 2, 9, 4, tzinfo=UTC), "2 Jan 2025, 09:04"),
    ],
)
def test_a_time_is_worded_by_how_long_ago_it_was(moment, text):
    assert when(moment, NOW, tz=UTC).text == text


def test_the_hover_title_and_the_datetime_attribute_are_exact():
    shown = when(datetime(2026, 11, 8, 12, 21, tzinfo=UTC), NOW, tz=UTC)

    assert shown.title == "8 Nov 2026, 12:21"
    assert shown.iso == "2026-11-08T12:21:00+00:00"


def test_days_are_counted_in_the_server_time_zone():
    just_after_midnight_there = datetime(2026, 11, 8, 22, 30, tzinfo=UTC)  # 00:30 on the 9th in +2
    now_there = datetime(2026, 11, 9, 5, 0, tzinfo=PLUS_TWO)  # still the 8th in UTC

    shown = when(just_after_midnight_there, now_there, tz=PLUS_TWO)

    assert shown.text == "Today, 00:30"
    assert shown.title == "9 Nov 2026, 00:30"


@pytest.mark.parametrize(
    ("seconds", "text"),
    [
        (0, "0.0 s"),
        (2.44, "2.4 s"),
        (59.94, "59.9 s"),
        (59.96, "1 min 0 s"),  # never "60.0 s"
        (60, "1 min 0 s"),
        (125.9, "2 min 6 s"),  # whole seconds, rounded
        (3600, "60 min 0 s"),
    ],
)
def test_a_duration_has_one_decimal_under_a_minute_and_whole_seconds_after(seconds, text):
    start = datetime(2026, 11, 8, 14, 0, tzinfo=UTC)

    assert took(start, start + timedelta(seconds=seconds)) == text


def test_a_duration_is_omitted_without_a_finish_time():
    assert took(NOW, None) is None
