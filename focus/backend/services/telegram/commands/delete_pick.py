from __future__ import annotations

from typing import Any

from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.telegram.formatters import format_task_line
from focus.backend.services.telegram.types import TelegramContext


async def render_delete_pick(
    ctx: TelegramContext, limit: int = 10
) -> tuple[str, dict[str, Any]]:
    repo = TaskRepo(ctx.db)
    tasks = await repo.list_user_tasks(
        user_id=ctx.telegram_user.id,
        status=None,
        tag=None,
        limit=limit,
        show_all=False,
    )

    if not tasks:
        text = "Задач нет — удалять нечего 🙂"
        kb = {
            "inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "today_refresh"}]]
        }
        return text, kb

    lines = ["Выбери задачу для удаления:"]
    for t in tasks:
        lines.append(f"- {format_task_line(t)}")

    kb = {
        "inline_keyboard": (
            [[{"text": f"🗑️ id:{t.id}", "callback_data": f"del:{t.id}"}] for t in tasks]
            + [[{"text": "⬅️ Назад", "callback_data": "today_refresh"}]]
        )
    }
    return "\n".join(lines), kb
