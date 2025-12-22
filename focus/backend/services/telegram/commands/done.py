from typing import Sequence

from sqlalchemy import select

from focus.backend.database import models
from focus.backend.database.enums import TaskStatus
from focus.backend.services.tasks import change_task_status
from focus.backend.services.telegram.api import send_reply
from focus.backend.services.telegram.formatters import format_task_line
from focus.backend.services.telegram.types import TelegramContext


async def command_done(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /done <id> — отметить задачу пользователя выполненной.
    """
    db = ctx.db
    telegram_user = ctx.telegram_user
    chat_id = ctx.chat_id

    if not args or not args[0].isdigit():
        await send_reply(chat_id, "Использование: /done <id>")
        return

    task_id = int(args[0])
    stmt = (
        select(models.Task)
        .where(
            models.Task.id == task_id,
            models.Task.user_id == telegram_user.id,
        )
        .limit(1)
    )
    task = db.execute(stmt).scalars().first()

    if not task:
        await send_reply(chat_id, f"Задача с id {task_id} не найдена")
        return

    if task.status == TaskStatus.DONE.value:
        await send_reply(chat_id, "Эта задача уже в статусе done ✅")
        return

    change_task_status(task, TaskStatus.DONE)
    db.commit()
    db.refresh(task)

    await send_reply(chat_id=chat_id, text=f"Готово: {format_task_line(task)}")
