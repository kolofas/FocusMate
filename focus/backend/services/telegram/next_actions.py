from __future__ import annotations

from focus.backend.database.enums import TaskStatus
from focus.backend.services.focus import get_plan_today
from focus.backend.services.telegram.formatters import format_task_line
from focus.backend.services.telegram.types import TelegramContext


async def suggest_next_action_line(ctx: TelegramContext) -> str:
    default = "Дальше: /today или /tasks planned"

    try:
        plan = await get_plan_today(
            ctx.db, user_id=ctx.telegram_user.id, ensure_build=True
        )
        remaining = [it for it in plan.items if it.task.status != TaskStatus.DONE.value]
        if remaining:
            it = sorted(remaining, key=lambda x: x.rank)[0]
            return f"Следующая сегодня: {it.rank}. {format_task_line(it.task)}"
        return "🎉 На сегодня всё. Хочешь взять ещё? /tasks planned"
    except Exception:
        return default
