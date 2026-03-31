from __future__ import annotations

from typing import Sequence

from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.telegram.screens.today_screen import refresh_today_screen
from focus.backend.services.telegram.types import TelegramContext


async def command_delete(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /del <id> - удалить задачу
    /rm <id> - алиас
    """
    if not args:
        await refresh_today_screen(ctx, notice="⚠️ Формат: /del <id>")
        return

    try:
        task_id = int(args[0])
    except ValueError:
        await refresh_today_screen(ctx, notice="⚠️ Формат: /del <id>")
        return

    repo = TaskRepo(ctx.db)
    task = await repo.get_user_task(task_id=task_id, user_id=ctx.telegram_user.id)
    if not task:
        await refresh_today_screen(ctx, notice=f"⚠️ Не нашёл задачу id={task_id}")
        return

    await repo.delete(task)
    await ctx.db.commit()

    await refresh_today_screen(ctx, notice=f"✅ Задача id={task_id} удалена")
