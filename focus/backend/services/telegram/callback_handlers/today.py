from __future__ import annotations

import logging

from focus.backend.services.telegram.api import edit_message_text
from focus.backend.services.telegram.commands.today import render_today
from focus.backend.services.telegram.types import TelegramContext

log = logging.getLogger(__name__)


async def handle_today_refresh_or_replan(
    ctx: TelegramContext,
    *,
    message_id: int | None,
) -> bool:
    text, kb = await render_today(ctx, args=[])
    log.info("tg.edit: chat_id=%s message_id=%s", ctx.chat_id, message_id)
    return await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
