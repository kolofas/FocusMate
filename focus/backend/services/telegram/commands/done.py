from typing import Sequence

from sqlalchemy import select

from focus.backend.database import models
from focus.backend.database.enums import TaskStatus
from focus.backend.services.tasks import change_task_status
from focus.backend.services.telegram.api import send_reply
from focus.backend.services.telegram.formatters import format_task_line
from focus.backend.services.telegram.next_actions import suggest_next_action_line
from focus.backend.services.telegram.types import TelegramContext


async def _get_user_task_or_none(
    ctx: TelegramContext, task_id: int
) -> models.Task | None:
    result = await ctx.db.execute(
        select(models.Task).where(
            models.Task.id == task_id,
            models.Task.user_id == ctx.telegram_user.id,
        )
    )
    return result.scalars().first()


def _build_done_reply(task: models.Task, old_status: str, next_line: str) -> str:
    return (
        f"Закрыта: {format_task_line(task)}\n"
        f"Изменение: {old_status} → {task.status}\n"
        f"{next_line}"
    )


async def command_done(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /done <id> — отметить задачу пользователя выполненной.
    """
    chat_id = ctx.chat_id

    if not args or not args[0].isdigit():
        await send_reply(chat_id, "Использование: /done <id>")
        return

    task_id = int(args[0])
    task = await _get_user_task_or_none(ctx, task_id)

    if not task:
        await send_reply(
            chat_id, f"Не нашёл задачу с id {task_id}. Попробуй /today или /tasks"
        )
        return

    old_status = task.status
    if old_status == TaskStatus.DONE.value:
        await send_reply(
            chat_id,
            f"Уже закрыта: {format_task_line(task)}\nДальше: /today или /tasks planned",
        )
        return

    await change_task_status(task, TaskStatus.DONE)

    await ctx.db.commit()
    await ctx.db.refresh(task)

    next_line = await suggest_next_action_line(ctx)
    await send_reply(chat_id, _build_done_reply(task, old_status, next_line))
