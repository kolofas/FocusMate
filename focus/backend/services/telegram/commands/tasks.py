from typing import Sequence

from focus.backend.repositories.tasks_repo import TaskRepo
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
    telegram_user = ctx.telegram_user
    chat_id = ctx.chat_id

    status, tag, limit, show_all = parse_task_filters(args)
    limit = limit or 5

    repo = TaskRepo(ctx.db)
    tasks = await repo.list_user_tasks(
        user_id=telegram_user.id,
        status=status,
        tag=tag,
        limit=limit,
        show_all=show_all,
    )

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
