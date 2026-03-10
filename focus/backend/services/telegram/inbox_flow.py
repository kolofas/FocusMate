from __future__ import annotations

from typing import Any

from zoneinfo import ZoneInfo


from focus.backend.database.enums import TaskSource, TaskStatus
from focus.backend.services.parsing import InboxParser
from focus.backend.services.tasks import create_task_from_parsed

from focus.backend.services.telegram.api import send_reply
from focus.backend.services.telegram.commands import COMMAND_HANDLERS
from focus.backend.services.telegram.types import TelegramContext

_parser = InboxParser(tz=ZoneInfo("Europe/Amsterdam"))


async def try_handle_command(text: str, ctx: TelegramContext) -> bool:
    """
    Пытается обработать Telegram-команду.
    True — команда обработана (включая неизвестную команду).
    False — не команда, обычный текст → в инбокс.
    """
    parts = text.split()
    if not parts:
        return False

    cmd, args = parts[0].lower(), parts[1:]
    handler = COMMAND_HANDLERS.get(cmd)
    if handler:
        await handler(ctx, args)
        return True

    if cmd.startswith("/"):
        await send_reply(ctx.chat_id, "Не знаю такую команду. Напиши /help")
        return True

    return False


async def process_inbox_text(text: str, ctx: TelegramContext) -> dict[str, Any]:
    """
    Базовый инбокс-флоу для входящего текста из Telegram:
      - dedup по source+text,
      - парсинг,
      - создание Task,
      - запись InboxEvent,
      - commit.
    """
    source = TaskSource.TELEGRAM
    db = ctx.db

    parsed = _parser.parse(text)

    task = await create_task_from_parsed(
        db,
        parsed,
        source=source,
        status=TaskStatus.INBOX,
        raw_text=text,
    )

    task.user_id = ctx.telegram_user.id

    await db.commit()
    await db.refresh(task)

    return {"ok": True, "duplicate": False, "task_id": task.id, "title": task.title}

    # dedup_key = make_dedup(text)
    # repo = InboxRepo(db)

    # if await repo.exists_recent(
    #     source=source.value,
    #     dedup_key=dedup_key,
    #     user_id=ctx.telegram_user.id,
    # ):
    #     return {"ok": True, "duplicate": True}

    # await repo.add(
    #     source=source.value,
    #     dedup_key=dedup_key,
    #     user_id=ctx.telegram_user.id,
    # )
