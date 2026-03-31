from __future__ import annotations

import logging

from focus.backend.services.telegram.screens.today_screen import refresh_today_screen
from focus.backend.services.telegram.types import TelegramContext

log = logging.getLogger(__name__)


async def handle_today_refresh_or_replan(
    ctx: TelegramContext,
    *,
    action: str,
    message_id: int | None,
) -> bool:
    rebuild_plan = action == "today_replan"
    await refresh_today_screen(
        ctx, preferred_message_id=message_id, rebuild_plan=rebuild_plan
    )
    return True
