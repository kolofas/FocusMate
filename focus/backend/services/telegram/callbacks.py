from __future__ import annotations
import logging

from focus.backend.services.telegram.types import TelegramContext
from focus.backend.services.telegram.api import (
    answer_callback_query,
)
from focus.backend.services.telegram.callback_handlers.today import (
    handle_today_refresh_or_replan,
)
from focus.backend.services.telegram.callback_handlers.tasks import handle_tasks_planned
from focus.backend.services.telegram.callback_handlers.add import handle_task_add
from focus.backend.services.telegram.callback_handlers.done import (
    handle_today_done_pick,
    handle_done_task,
)


log = logging.getLogger(__name__)


async def handle_callback(
    data: str,
    ctx: TelegramContext,
    callback_query_id: str | None,
    message_id: int | None,
) -> bool:
    """
    Returns True if handled.
    """
    if data in ("today_refresh", "today_replan"):
        changed = await handle_today_refresh_or_replan(ctx, message_id=message_id)
        if not changed:
            msg = "Без изменений" if data == "today_refresh" else "План уже оптимален"
            await answer_callback_query(callback_query_id, text=msg)
        else:
            await answer_callback_query(callback_query_id)
        return True

    if data == "today_done_pick":
        await handle_today_done_pick(
            ctx, callback_query_id=callback_query_id, message_id=message_id
        )
        return True

    if data.startswith("done:"):
        try:
            task_id = int(data.split(":", 1)[1])
        except ValueError:
            await answer_callback_query(
                callback_query_id, text="Некорректный id", show_alert=True
            )
            return True

        await handle_done_task(
            ctx,
            task_id=task_id,
            callback_query_id=callback_query_id,
            message_id=message_id,
        )
        return True

    if data == "tasks_planned":
        await handle_tasks_planned(ctx)
        await answer_callback_query(callback_query_id)
        return True

    if data == "task_add":
        await handle_task_add(ctx)
        await answer_callback_query(callback_query_id)
        return True

    return False
