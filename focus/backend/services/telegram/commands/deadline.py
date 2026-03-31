from __future__ import annotations

from datetime import datetime
from typing import Sequence
from zoneinfo import ZoneInfo

from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.telegram.screens.today_screen import refresh_today_screen
from focus.backend.services.telegram.types import TelegramContext
from focus.backend.utils.datetime import to_utc

_LOCAL_TZ = ZoneInfo("Europe/Amsterdam")
_CLEAR_MARKERS = {"clear", "none", "-"}


def _parse_deadline_args(
    args: Sequence[str],
) -> tuple[int | None, datetime | None, bool]:
    """
    /deadline <id> <YYYY-MM-DD[ HH:MM]>
    /deadline <id> clear
    Returns: (task_id, deadline_utc_or_none, ok)
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
                hour=23,
                minute=59,
                tzinfo=_LOCAL_TZ,
            )
            return task_id, to_utc(dt_local), True

        dt_local = datetime.strptime(normalized, "%Y-%m-%d %H:%M").replace(
            tzinfo=_LOCAL_TZ
        )
        return task_id, to_utc(dt_local), True
    except ValueError:
        return None, None, False


async def command_deadline(ctx: TelegramContext, args: Sequence[str]) -> None:
    task_id, deadline_utc, ok = _parse_deadline_args(args)
    if not ok or task_id is None:
        await refresh_today_screen(ctx)
        return

    repo = TaskRepo(ctx.db)
    task = await repo.get_user_task(task_id=task_id, user_id=ctx.telegram_user.id)
    if not task:
        await refresh_today_screen(ctx)
        return

    task.deadline = deadline_utc
    await ctx.db.commit()

    await refresh_today_screen(ctx, rebuild_plan=True)
