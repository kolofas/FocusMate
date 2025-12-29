from __future__ import annotations


from focus.backend.services.telegram.types import TelegramContext
from focus.backend.services.telegram.api import answer_callback_query
from focus.backend.services.telegram.commands.today import command_today


async def handle_callback(
    data: str, ctx: TelegramContext, callback_query_id: str | None
) -> bool:
    """
    Returns True if handled.
    """
    await answer_callback_query(callback_query_id)

    if data == "today_refresh":
        await command_today(ctx, args=[])
        return True

    if data == "today_replan":
        await command_today(ctx, args=[])
        return True

    return False
