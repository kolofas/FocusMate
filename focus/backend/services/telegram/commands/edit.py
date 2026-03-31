from __future__ import annotations

from typing import Sequence

from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.telegram.screens.today_screen import refresh_today_screen
from focus.backend.services.telegram.types import TelegramContext
from focus.backend.settings import settings


def _parse_edit_args(args: Sequence[str]) -> tuple[int | None, str | None]:
    """
    /edit <id> <new title>
    """
    if len(args) < 2 or not args[0].isdigit():
        return None, None

    task_id = int(args[0])
    new_title = " ".join(args[1:]).strip()
    if not new_title:
        return None, None

    return task_id, new_title


async def command_edit(ctx: TelegramContext, args: Sequence[str]) -> None:
    task_id, new_title = _parse_edit_args(args)
    if task_id is None or new_title is None:
        await refresh_today_screen(ctx)
        return

    repo = TaskRepo(ctx.db)
    task = await repo.get_user_task(task_id=task_id, user_id=ctx.telegram_user.id)
    if not task:
        await refresh_today_screen(ctx)
        return

    normalized_title = new_title[: settings.max_title_length].strip()
    if not normalized_title:
        await refresh_today_screen(ctx)
        return

    if task.title == normalized_title:
        await refresh_today_screen(ctx)
        return

    task.title = normalized_title
    await ctx.db.commit()

    await refresh_today_screen(ctx)
