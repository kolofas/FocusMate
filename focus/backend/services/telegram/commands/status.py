from typing import Sequence

from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.tasks import change_task_status
from focus.backend.services.telegram.api import send_reply
from focus.backend.services.telegram.screens.today_screen import refresh_today_screen
from focus.backend.services.telegram.formatters import format_task_line
from focus.backend.services.telegram.next_actions import suggest_next_action_line
from focus.backend.services.telegram.parsers import parse_status
from focus.backend.services.telegram.types import TelegramContext


def _parse_status_args(args: Sequence[str]) -> tuple[int | None, str | None]:
    if len(args) < 2 or not args[0].isdigit():
        return None, None
    return int(args[0]), args[1]


async def command_status(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /status <id> <st> — изменить статус задачи (inbox|planned|done|snoozed).
    """
    user_id = ctx.telegram_user.id
    chat_id = ctx.chat_id

    task_id, status_raw = _parse_status_args(args)
    if task_id is None or status_raw is None:
        await send_reply(
            chat_id, "Использование: /status <id> <inbox|planned|done|snoozed>"
        )
        return

    new_status = parse_status(status_raw)
    if not new_status:
        await send_reply(
            chat_id, "Неизвестный статус. Используй: inbox | planned | done | snoozed"
        )
        return

    repo = TaskRepo(ctx.db)
    task = await repo.get_user_task(task_id=task_id, user_id=user_id)

    if not task:
        await send_reply(
            chat_id, f"Не нашёл задачу с id {task_id}. Попробуй /today или /tasks"
        )
        return

    before = task.status
    if before == new_status.value:
        await send_reply(
            chat_id,
            f"Статус уже {new_status.value}: {format_task_line(task)}\n{await suggest_next_action_line(ctx)}",
        )
        return

    await change_task_status(task, new_status)
    await ctx.db.commit()

    await refresh_today_screen(ctx)
