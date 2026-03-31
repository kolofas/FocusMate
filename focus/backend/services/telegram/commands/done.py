from typing import Sequence

from focus.backend.database.enums import TaskStatus
from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.tasks import change_task_status
from focus.backend.services.telegram.types import TelegramContext
from focus.backend.services.telegram.screens.today_screen import refresh_today_screen


async def command_done(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /done <id> — отметить задачу пользователя выполненной.
    """
    if not args or not args[0].isdigit():
        await refresh_today_screen(ctx, notice="⚠️ Формат: /done <id>")
        return

    task_id = int(args[0])

    repo = TaskRepo(ctx.db)
    task = await repo.get_user_task(task_id=task_id, user_id=ctx.telegram_user.id)

    if not task:
        await refresh_today_screen(ctx, notice=f"⚠️ Не нашёл задачу id={task_id}")
        return

    if task.status == TaskStatus.DONE.value:
        await refresh_today_screen(ctx, notice="ℹ️ Уже закрыта")
        return

    await change_task_status(task, TaskStatus.DONE)
    await ctx.db.commit()

    await refresh_today_screen(ctx, notice=f"✅ Задача id={task_id} закрыта")
