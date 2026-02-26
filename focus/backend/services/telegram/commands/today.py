from typing import Sequence

from focus.backend.services.telegram.types import TelegramContext
from focus.backend.services.telegram.screens.today_screen import refresh_today_screen


async def command_today(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /today [status] [all]
    """
    await refresh_today_screen(ctx, args=args)
