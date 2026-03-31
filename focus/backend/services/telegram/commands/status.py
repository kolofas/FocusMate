from typing import Sequence

from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.tasks import change_task_status
from focus.backend.services.telegram.screens.today_screen import refresh_today_screen
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

    task_id, status_raw = _parse_status_args(args)
    if task_id is None or status_raw is None:
        await refresh_today_screen(ctx)
        return

    new_status = parse_status(status_raw)
    if not new_status:
        await refresh_today_screen(ctx)
        return

    repo = TaskRepo(ctx.db)
    task = await repo.get_user_task(task_id=task_id, user_id=user_id)
    if not task:
        await refresh_today_screen(ctx)
        return

    if task.status == new_status.value:
        await refresh_today_screen(ctx)
        return

    await change_task_status(task, new_status)
    await ctx.db.commit()

    await refresh_today_screen(ctx, rebuild_plan=True)
