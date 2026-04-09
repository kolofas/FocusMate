from __future__ import annotations

from datetime import datetime
from typing import Sequence
from zoneinfo import ZoneInfo

from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.settings import settings
from focus.backend.services.telegram.screens.today_screen import refresh_today_screen
from focus.backend.services.telegram.types import TelegramContext
from focus.backend.utils.datetime import to_utc

_CLEAR_MARKERS = {"clear", "none", "-"}


def _parse_remind_args(
    args: Sequence[str],
    *,
    local_tz: ZoneInfo,
) -> tuple[int | None, datetime | None, bool]:
    """
    /remind <id> <YYYY-MM-DD[ HH:MM]>
    /remind <id> clear
    Returns: (task_id, reminder_at_utc_or_none, ok)
    """
    if len(args) < 2 or not args[0].isdigit():
        return None, None, False

    task_id = int(args[0])
    raw = " ".join(args[1:]).strip()
    if not raw:
        return None, None, False

    if raw.lower() in _CLEAR_MARKERS:
        return task_id, None, True

    normalized = raw.replace("T", " ")
    try:
        if len(normalized) == 10:
            dt_local = datetime.strptime(normalized, "%Y-%m-%d").replace(
                hour=9,
                minute=0,
                tzinfo=local_tz,
            )
            return task_id, to_utc(dt_local), True

        dt_local = datetime.strptime(normalized, "%Y-%m-%d %H:%M").replace(
            tzinfo=local_tz
        )
        return task_id, to_utc(dt_local), True
    except ValueError:
        return None, None, False


def _get_app_tz() -> ZoneInfo:
    try:
        return ZoneInfo(settings.app_timezone)
    except Exception:
        return ZoneInfo("UTC")


async def command_remind(ctx: TelegramContext, args: Sequence[str]) -> None:
    app_tz = _get_app_tz()
    task_id, reminder_at_utc, ok = _parse_remind_args(args, local_tz=app_tz)
    if not ok or task_id is None:
        await refresh_today_screen(
            ctx,
            notice="⚠️ Формат: /remind <id> <YYYY-MM-DD[ HH:MM]|clear>",
        )
        return

    repo = TaskRepo(ctx.db)
    task = await repo.get_user_task(task_id=task_id, user_id=ctx.telegram_user.id)
    if not task:
        await refresh_today_screen(ctx, notice=f"⚠️ Не нашёл задачу id={task_id}")
        return

    task.reminder_at = reminder_at_utc
    if reminder_at_utc is None:
        task.reminder_sent_at = None
        notice = f"✅ Напоминание для id={task_id} сброшено"
    else:
        task.reminder_sent_at = None
        local_dt = reminder_at_utc.astimezone(app_tz)
        notice = (
            f"✅ Напоминание для id={task_id} установлено: "
            f"{local_dt.strftime('%Y-%m-%d %H:%M')} ({settings.app_timezone})"
        )
    await ctx.db.commit()

    await refresh_today_screen(ctx, rebuild_plan=True, notice=notice)
