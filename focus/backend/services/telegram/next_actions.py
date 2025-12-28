from __future__ import annotations

import logging

from focus.backend.database.enums import TaskStatus
from focus.backend.services.focus import get_plan_today
from focus.backend.services.telegram.formatters import format_task_line
from focus.backend.services.telegram.types import TelegramContext

log = logging.getLogger(__name__)


_DEFAULT = "Дальше: /today или /tasks planned"
_ALL_DONE = "🎉 На сегодня всё. Хочешь взять ещё? /tasks planned"


async def suggest_next_action_line(ctx: TelegramContext) -> str:
    try:
        plan = await get_plan_today(
            ctx.db, user_id=ctx.telegram_user.id, ensure_build=True
        )

        remaining = [it for it in plan.items if it.task.status != TaskStatus.DONE.value]

        if not remaining:
            return _ALL_DONE

        next_item = min(remaining, key=lambda x: x.rank)
        return (
            f"Следующая сегодня: {next_item.rank}. {format_task_line(next_item.task)}"
        )

    except Exception:
        log.exception("Failed to suggest next action")
        return _DEFAULT
