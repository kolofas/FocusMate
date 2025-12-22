from typing import Sequence

from sqlalchemy import select

from focus.backend.database import models
from focus.backend.services.telegram.api import send_reply
from focus.backend.services.telegram.formatters import format_task_line
from focus.backend.services.telegram.parsers import parse_task_filters
from focus.backend.services.telegram.types import TelegramContext


async def command_tasks(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /tasks [limit] [status] [#tag] [all]
    Примеры:
      /tasks
      /tasks 10
      /tasks planned
      /tasks #work
      /tasks 10 planned #work
      /tasks planned all
    """
    db = ctx.db
    telegram_user = ctx.telegram_user
    chat_id = ctx.chat_id

    status, tag, limit, show_all = parse_task_filters(args)
    limit = limit or 5

    stmt = (
        select(models.Task)
        .where(models.Task.user_id == telegram_user.id)
        .order_by(models.Task.created_at.desc())
    )
    if status:
        stmt = stmt.where(models.Task.status == status)
    if tag:
        stmt = stmt.where(models.Task.tags.contains([tag]))

    if not show_all:
        stmt = stmt.limit(limit)

    tasks = db.execute(stmt).scalars().all()
    if not tasks:
        await send_reply(chat_id, "Задач пока нет.")
        return

    head = "Последние задачи"
    filters: list[str] = []
    if status:
        filters.append(status)
    if tag:
        filters.append(f"#{tag}")
    if show_all:
        filters.append("all")
    if filters:
        head += f" ({', '.join(filters)})"

    lines = [head + ":"]
    for t in tasks:
        lines.append(f"- {format_task_line(t)}")

    await send_reply(chat_id, "\n".join(lines))
