from __future__ import annotations

from typing import Any

from focus.backend.database.enums import TaskStatus
from focus.backend.services.focus import get_plan_today
from focus.backend.services.telegram.types import TelegramContext


def _inline_kb(rows: list[list[tuple[str, str]]]) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": t, "callback_data": d} for (t, d) in row] for row in rows
        ]
    }


async def render_done_pick(
    ctx: TelegramContext, *, limit: int = 8
) -> tuple[str, dict[str, Any]]:
    """
    Возвращает текст + клавиатуру выбора задачи для закрытия.
    """
    plan = await get_plan_today(ctx.db, user_id=ctx.telegram_user.id, ensure_build=True)
    remaining = [it for it in plan.items if it.task.status != TaskStatus.DONE]
    remaining = sorted(remaining, key=lambda x: x.rank)[:limit]

    if not remaining:
        text = "На сегодня нечего закрывать ✅"
        kb = _inline_kb([[("↩️ Назад", "today_refresh")]])
        return text, kb

    lines = ["Что закрываем?"]
    rows: list[list[tuple[str, str]]] = []

    for it in remaining:
        title = (it.task.title or "").strip()
        if len(title) > 32:
            title = title[:29] + "..."
        btn_text = f"{it.rank}. {title}"
        rows.append([(btn_text, f"done:{it.task.id}")])

    rows.append([("↩️ Назад", "today_refresh"), ("📋 Сегодня", "today_refresh")])

    return "\n".join(lines), _inline_kb(rows)
