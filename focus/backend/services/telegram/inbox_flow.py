from __future__ import annotations

from typing import Any

from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from focus.backend.database.enums import TaskSource, TaskStatus
from focus.backend.services import (
    InboxParser,
    make_dedup,
    is_duplicate_inbox,
    create_task_from_parsed,
    save_inbox_event,
)
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


def process_inbox_text(text: str, ctx: TelegramContext) -> dict[str, Any]:
    """
    Базовый инбокс-флоу для входящего текста из Telegram:
      - dedup по source+text,
      - парсинг,
      - создание Task,
      - запись InboxEvent,
      - commit.
    """
    source = TaskSource.TELEGRAM
    dedup_key = make_dedup(text)
    db = ctx.db

    if is_duplicate_inbox(db, source.value, dedup_key):
        return {"ok": True, "duplicate": True}

    parsed = _parser.parse(text)
    task = create_task_from_parsed(
        db,
        parsed,
        source=source,
        status=TaskStatus.INBOX,
        raw_text=text,
    )
    task.user_id = ctx.telegram_user.id

    event = save_inbox_event(db, source.value, dedup_key)
    event.user_id = ctx.telegram_user.id

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"ok": True, "duplicate": True}

    db.refresh(task)
    return {"ok": True, "duplicate": False, "task_id": task.id, "title": task.title}
