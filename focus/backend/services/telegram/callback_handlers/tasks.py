from __future__ import annotations

from focus.backend.services.telegram.commands.tasks import command_tasks
from focus.backend.services.telegram.types import TelegramContext


async def handle_tasks_planned(ctx: TelegramContext) -> None:
    await command_tasks(ctx, args=["planned"])
