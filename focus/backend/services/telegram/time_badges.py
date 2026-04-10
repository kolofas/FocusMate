from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol
from zoneinfo import ZoneInfo

from focus.backend.settings import settings


class TaskWithTiming(Protocol):
    deadline: datetime | None
    reminder_at: datetime | None


def _get_app_tz() -> ZoneInfo:
    try:
        return ZoneInfo(settings.app_timezone)
    except Exception:
        return ZoneInfo("UTC")


def _format_local_dt(value: datetime) -> str:
    tz = _get_app_tz()
    local_dt = value.astimezone(tz)
    today = datetime.now(tz).date()
    target_day = local_dt.date()

    if target_day == today:
        return f"сегодня {local_dt.strftime('%H:%M')}"
    if target_day == today + timedelta(days=1):
        return f"завтра {local_dt.strftime('%H:%M')}"
    return local_dt.strftime("%d.%m %H:%M")


def format_task_time_badges(task: TaskWithTiming) -> str:
    parts: list[str] = []

    if task.deadline:
        parts.append(f"⏳ {_format_local_dt(task.deadline)}")

    if task.reminder_at:
        parts.append(f"⏰ {_format_local_dt(task.reminder_at)}")

    if not parts:
        return ""
    return " • " + " • ".join(parts)
