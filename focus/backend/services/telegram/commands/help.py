from typing import Sequence

from focus.backend.services.telegram.api import send_reply
from focus.backend.services.telegram.consts import HELP_TEXT
from focus.backend.services.telegram.types import TelegramContext


async def command_help(ctx: TelegramContext, args: Sequence[str]) -> None:
    await send_reply(ctx.chat_id, HELP_TEXT)
