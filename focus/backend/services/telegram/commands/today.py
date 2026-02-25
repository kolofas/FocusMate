from typing import Sequence, Any

from focus.backend.database.enums import TaskStatus
from focus.backend.services.focus import get_plan_today
from focus.backend.services.telegram.api import send_or_edit
from focus.backend.services.telegram.consts import STATUS_EMOJI
from focus.backend.services.telegram.next_actions import (
    today_keyboard,
    suggest_next_action_line,
)
from focus.backend.services.telegram.parsers import parse_today_filters
from focus.backend.services.telegram.types import TelegramContext


async def render_today(
    ctx: TelegramContext, args: Sequence[str]
) -> tuple[str, dict[str, Any]]:
    db = ctx.db
    telegram_user = ctx.telegram_user

    status_filter, include_done = parse_today_filters(args)

    plan = await get_plan_today(db, user_id=telegram_user.id, ensure_build=True)
    items = list(plan.items)

    if status_filter:
        items = [it for it in items if it.task.status == status_filter]

    if not include_done:
        items = [it for it in items if it.task.status != TaskStatus.DONE.value]

    if not items:
        if status_filter:
            text = f"В фокусе на сегодня нет задач со статусом {status_filter}" + (
                "" if not include_done else " (включая done)."
            )
        else:
            text = "На сегодня задач нет.\n\nПопробуй:\n• ➕ добавить задачу\n• 🧠 собрать план на день"
        return text, today_keyboard(has_items=False)

    header = f"Сегодня • {plan.date}"
    suffix_parts: list[str] = []
    if status_filter:
        suffix_parts.append(status_filter)
    if include_done:
        suffix_parts.append("all")
    if suffix_parts:
        header += " (" + ", ".join(suffix_parts) + ")"

    lines = [header]
    for item in items:
        emoji = STATUS_EMOJI.get(item.task.status, "•")
        lines.append(
            f"{item.rank}. {emoji} [id: {item.task.id}] {item.task.title} ({item.score}🔸)"
        )

    lines.append("")
    lines.append(await suggest_next_action_line(ctx))
    lines.append("")
    lines.append("Закрыть: /done <id> • Статус: /status <id> planned")

    return "\n".join(lines), today_keyboard(has_items=True)


async def command_today(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /today [status] [all] — фокус-лист на сегодня для пользователя.
    Примеры:
      /today
      /today planned
      /today planned all
      /today all
    """
    text, kb = await render_today(ctx, args)

    telegram_user = ctx.telegram_user
    new_message_id = await send_or_edit(
        ctx.chat_id,
        telegram_user.screen_message_id,
        text,
        reply_markup=kb,
    )

    if new_message_id and new_message_id != telegram_user.screen_message_id:
        telegram_user.screen_message_id = new_message_id
        await ctx.db.commit()
