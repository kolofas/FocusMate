from typing import Sequence

from sqlalchemy import select

from focus.backend.database import models
from focus.backend.services.tasks import change_task_status
from focus.backend.services.telegram.api import send_reply
from focus.backend.services.telegram.formatters import format_task_line
from focus.backend.services.telegram.parsers import parse_status
from focus.backend.services.telegram.types import TelegramContext


async def command_status(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /status <id> <st> — изменить статус задачи (inbox|planned|done|snoozed).
    """
    db = ctx.db
    telegram_user = ctx.telegram_user
    chat_id = ctx.chat_id

    if len(args) < 2 or not args[0].isdigit():
        await send_reply(
            chat_id, "Использование: /status <id> <inbox|planned|done|snoozed>"
        )
        return

    task_id = int(args[0])
    new_status = parse_status(args[1])

    if not new_status:
        await send_reply(
            chat_id,
            "Неизвестный статус. Используй: inbox | planned | done | snoozed",
        )
        return

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

    if task.status == new_status.value:
        await send_reply(chat_id, f"Статус уже {new_status.value}.")
        return

    change_task_status(task, new_status)
    db.commit()
    db.refresh(task)

    await send_reply(chat_id, f"Статус обновлён: {format_task_line(task)}")
