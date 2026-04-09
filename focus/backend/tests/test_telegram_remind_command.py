from datetime import timedelta

from focus.backend.services.telegram.commands.remind import _parse_remind_args


def test_parse_remind_args_date_only_sets_0900_utc():
    task_id, reminder_at, ok = _parse_remind_args(["12", "2026-04-10"])
    assert ok is True
    assert task_id == 12
    assert reminder_at is not None
    assert reminder_at.utcoffset() == timedelta(0)
    # Europe/Amsterdam 09:00 -> UTC 07:00 (DST period in April)
    assert reminder_at.hour == 7 and reminder_at.minute == 0


def test_parse_remind_args_datetime_works():
    task_id, reminder_at, ok = _parse_remind_args(["7", "2026-04-10", "10:30"])
    assert ok is True
    assert task_id == 7
    assert reminder_at is not None
    assert reminder_at.utcoffset() == timedelta(0)


def test_parse_remind_args_clear():
    task_id, reminder_at, ok = _parse_remind_args(["7", "clear"])
    assert ok is True
    assert task_id == 7
    assert reminder_at is None


def test_parse_remind_args_invalid():
    assert _parse_remind_args([]) == (None, None, False)
    assert _parse_remind_args(["7"]) == (None, None, False)
    assert _parse_remind_args(["abc", "2026-04-10"]) == (None, None, False)
    assert _parse_remind_args(["7", "10-04-2026"]) == (None, None, False)
