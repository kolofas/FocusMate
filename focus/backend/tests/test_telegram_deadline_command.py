from datetime import timedelta
from zoneinfo import ZoneInfo

from focus.backend.services.telegram.commands.deadline import _parse_deadline_args

_TZ = ZoneInfo("Europe/Amsterdam")


def test_parse_deadline_args_date_only_sets_2359_utc():
    task_id, deadline, ok = _parse_deadline_args(["12", "2026-04-01"], local_tz=_TZ)
    assert ok is True
    assert task_id == 12
    assert deadline is not None
    assert deadline.utcoffset() == timedelta(0)
    # Europe/Amsterdam 23:59 -> UTC 21:59 (DST period in April)
    assert deadline.hour == 21 and deadline.minute == 59


def test_parse_deadline_args_datetime_works():
    task_id, deadline, ok = _parse_deadline_args(
        ["7", "2026-04-01", "10:30"], local_tz=_TZ
    )
    assert ok is True
    assert task_id == 7
    assert deadline is not None
    assert deadline.utcoffset() == timedelta(0)


def test_parse_deadline_args_clear():
    task_id, deadline, ok = _parse_deadline_args(["7", "clear"], local_tz=_TZ)
    assert ok is True
    assert task_id == 7
    assert deadline is None


def test_parse_deadline_args_invalid():
    assert _parse_deadline_args([], local_tz=_TZ) == (None, None, False)
    assert _parse_deadline_args(["7"], local_tz=_TZ) == (None, None, False)
    assert _parse_deadline_args(["abc", "2026-04-01"], local_tz=_TZ) == (
        None,
        None,
        False,
    )
    assert _parse_deadline_args(["7", "01-04-2026"], local_tz=_TZ) == (
        None,
        None,
        False,
    )
