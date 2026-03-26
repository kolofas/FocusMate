from __future__ import annotations

from focus.backend.services.telegram.api import answer_callback_query, edit_message_text
from focus.backend.services.telegram.screens.today_screen import resolve_screen_message_id
from focus.backend.services.telegram.types import TelegramContext


async def handle_task_add(
    ctx: TelegramContext,
    *,
    callback_query_id: str | None,
    message_id: int | None,
) -> None:
    text = (
        "Ок. Просто напиши текст задачи следующим сообщением — я добавлю в инбокс.\n\n"
        "Пример: Купить воду"
    )
    kb = {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "today_refresh"}]]}
    target_message_id = resolve_screen_message_id(ctx, message_id)
    await edit_message_text(ctx.chat_id, target_message_id, text, reply_markup=kb)
    await answer_callback_query(callback_query_id)
