from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from ..database import models
from ..database.enums import TaskSource, TaskStatus
from ..services import (
    InboxParser,
    create_task_from_parsed,
    is_duplicate_inbox,
    make_dedup,
    save_inbox_event,
)

from .telegram.types import TelegramContext
from .telegram.api import send_reply
from .telegram.commands import COMMAND_HANDLERS

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


def process_inbox_text(
    db: Session,
    text: str,
    *,
    telegram_user: models.TelegramUser | None = None,
) -> dict[str, Any]:
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
    if telegram_user:
        task.user_id = telegram_user.id

    event = save_inbox_event(db, source.value, dedup_key)
    if telegram_user:
        event.user_id = telegram_user.id

    db.commit()
    db.refresh(task)

    return {"ok": True, "duplicate": False, "task_id": task.id, "title": task.title}
