from __future__ import annotations


import logging
from typing import Any

from focus.backend.database.enums import TaskStatus
from focus.backend.services.focus import get_plan_today
from focus.backend.services.telegram.formatters import format_task_line
from focus.backend.services.telegram.types import TelegramContext

log = logging.getLogger(__name__)


_DEFAULT = "Дальше: /today или /tasks planned"
_ALL_DONE = "🎉 На сегодня всё. Хочешь взять ещё? /tasks planned"


def _inline_keyboard(rows: list[list[tuple[str, str]]]) -> dict[str, Any]:
    """
    rows: [[(text, callback_or_command), ...], ...]
    Мы используем callback_data ТОЛЬКО если у тебя есть обработчик callback'ов.
    Если пока нет — безопаснее класть команды в текст и/или использовать switch_inline_query_current_chat.
    """
    return {
        "inline_keyboard": [
            [{"text": btn_text, "callback_data": data} for (btn_text, data) in row]
            for row in rows
        ]
    }


def today_keyboard(*, has_items: bool) -> dict[str, Any]:
    if has_items:
        return _inline_keyboard(
            [
                [
                    ("✅ Done…", "today_done_pick"),
                    ("🗑️ Delete…", "today_delete_pick"),
                    ("📋 Обновить", "today_refresh"),
                ],
                [("➕ Добавить", "task_add"), ("🧠 Replan", "today_replan")],
                [("📦 Planned", "tasks_planned")],
            ]
        )
    return _inline_keyboard(
        [
            [("➕ Добавить", "task_add"), ("🧠 Собрать план", "today_replan")],
            [("📦 Planned", "tasks_planned")],
        ]
    )


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
