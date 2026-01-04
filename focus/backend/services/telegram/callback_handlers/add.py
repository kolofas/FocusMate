from __future__ import annotations

from focus.backend.services.telegram.api import send_reply
from focus.backend.services.telegram.types import TelegramContext


async def handle_task_add(ctx: TelegramContext) -> None:
    await send_reply(
        ctx.chat_id,
        "Ок. Просто напиши текст задачи следующим сообщением — я добавлю в инбокс.\n\n"
        "Пример: `Купить воду`",
        parse_mode="Markdown",
    )
