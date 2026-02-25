from __future__ import annotations

from focus.backend.services.telegram.api import send_or_edit
from focus.backend.services.telegram.commands.today import render_today
from focus.backend.services.telegram.types import TelegramContext


async def refresh_today_screen(ctx: TelegramContext) -> None:
    """
    Перерисовывать экран /today  в одном и том же сообщении (editMessageText),
    с fallback на sendMessage, и сохраняет screen_message_id в telegram_user
    """
    text, kb = await render_today(ctx, args=[])
    tg_user = ctx.telegram_user

    new_message_id = await send_or_edit(
        ctx.chat_id,
        tg_user.screen_message_id,
        text,
        reply_markup=kb,
    )

    if new_message_id and new_message_id != tg_user.screen_message_id:
        tg_user.screen_message_id = new_message_id
        await ctx.db.commit()