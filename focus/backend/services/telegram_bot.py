from __future__ import annotations

from typing import Any, Optional, Sequence, Callable, Awaitable

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from .tasks import change_task_status
from ..database import models
from ..database.enums import TaskSource, TaskStatus
from ..services import (
    InboxParser,
    create_task_from_parsed,
    is_duplicate_inbox,
    make_dedup,
    save_inbox_event,
)
from ..services.focus import get_plan_today
from ..settings import settings

_parser = InboxParser(tz=ZoneInfo("Europe/Amsterdam"))

HELP_TEXT = (
    "🌟 FocusMate — быстрый инбокс задач\n\n"
    "Команды:\n"
    "/today            — фокус-лист на сегодня\n"
    "/tasks            — последние задачи (с фильтрами)\n"
    "/done <id>        — отметить задачу выполненной\n"
    "/status <id> <st> — изменить статус (inbox|planned|done|snoozed)\n"
    "/help             — эта справка\n\n"
    "Фильтры для /tasks:\n"
    "  /tasks planned         — только planned\n"
    "  /tasks #work           — по тегу\n"
    "  /tasks 10 planned      — лимит + статус\n"
    "  /tasks planned #work   — комбинированно\n"
    "  /tasks planned all     — все задачи этого статуса\n\n"
    "Добавить задачу: просто напиши текст.\n"
    "Примеры:\n"
    "• купить молоко 2025-12-31\n"
    "• починить баг #urgent"
)

_ALLOWED_STATUS = {s.value for s in TaskStatus}

STATUS_EMOJI = {
    TaskStatus.INBOX.value: "📥",
    TaskStatus.PLANNED.value: "🧭",
    TaskStatus.DONE.value: "✅",
    TaskStatus.SNOOZED.value: "⏸️",
}


def _parse_status(value: str) -> TaskStatus | None:
    value = value.strip().lower()
    for st in TaskStatus:
        if st.value == value:
            return st
    return None


def _format_task_line(task: models.Task) -> str:
    """
    Строка задачи для Telegram:
    '🧭 [id:4] купить молоко [planned] #home'
    """
    emoji = STATUS_EMOJI.get(task.status, "•")
    base = f"{emoji} [id:{task.id}] {task.title} [{task.status}]"
    if task.tags:
        tags_part = " ".join(f"#{t}" for t in task.tags)
        return f"{base} {tags_part}"
    return base


def _parse_task_filters(args: Sequence[str]) -> tuple[Optional[str], Optional[str], Optional[int], bool]:
    """
    Разбирает аргументы /tasks:
      статус (inbox/planned/done/snoozed),
      тег (#work),
      лимит (целое число),
      флаг all (показать все, без лимита).
    Возвращает (status, tag, limit, show_all).
    """
    status: Optional[str] = None
    tag: Optional[str] = None
    limit: Optional[int] = None
    show_all = False

    for raw in args:
        arg = raw.strip().lower()
        if not arg:
            continue
        if arg == "all":
            show_all = True
        elif arg.isdigit():
            value = int(arg)
            if value > 0:
                limit = value
        elif arg.startswith("#"):
            tag = arg.lstrip("#")
        elif arg in _ALLOWED_STATUS:
            status = arg

    return status, tag, limit, show_all


def _parse_today_filters(args: Sequence[str]) -> tuple[Optional[str], bool]:
    """
    Для /today поддерживаем:
      /today                 -> без фильтров, без done
      /today planned         -> только planned, без done
      /today planned all     -> только planned, с учётом done
      /today all             -> все статусы, включая done
    Возвращает (status_filter, include_done).
    """
    status: Optional[str] = None
    include_done = False

    for raw in args:
        argument = raw.strip().lower()
        if not argument:
            continue

        if argument in _ALLOWED_STATUS:
            status = argument
        elif argument == "all":
            include_done = True

    return status, include_done


def extract_text_and_chat_id(update: dict[str, Any]) -> tuple[Optional[str], Optional[int], dict[str, Any]]:
    """
    Достаёт текст и chat_id из апдейта Telegram.
    Поддерживает message/edited_message.
    """
    msg = update.get("message") or update.get("edited_message") or {}
    text = (msg.get("text") or "").strip()

    from_block = msg.get("from") or {}
    meta = {
        "username": from_block.get("username"),
        "first_name": from_block.get("first_name"),
    }

    chat = msg.get("chat") or {}
    chat_id = chat.get("id")

    if not text:
        return None, None, meta
    return text, chat_id, meta


async def send_reply(chat_id: Optional[int], text: str) -> None:
    """
    Отправляет ответ пользователю.
    Ошибки доставки не пробрасываем — вебхук важнее.
    """
    if not chat_id:
        return

    token = settings.telegram_bot_token
    if not token:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(url, json=payload)
    except Exception:
        # TODO: логировать, но не падать
        pass


async def _command_help(
    chat_id: int | None,
    db: Session,
    telegram_user: models.TelegramUser,
    args: Sequence[str],
) -> None:
    await send_reply(chat_id, HELP_TEXT)


async def _command_today(
    chat_id: int | None,
    db: Session,
    telegram_user: models.TelegramUser,
    args: Sequence[str],
) -> None:
    """
    /today [status] [all] — фокус-лист на сегодня для пользователя.
    Примеры:
      /today
      /today planned
      /today planned all
      /today all
    """
    status_filter, include_done = _parse_today_filters(args)

    plan = get_plan_today(db, user_id=telegram_user.id, ensure_build=True)
    items = list(plan.items)

    if status_filter:
        items = [it for it in items if it.task.status == status_filter]

    if not include_done:
        items = [it for it in items if it.task.status != TaskStatus.DONE.value]

    if not items:
        if status_filter:
            await send_reply(
                chat_id,
                f"В фокусе на сегодня нет задач со статусом {status_filter}"
                + ("" if not include_done else " (включая done)."),
            )
        else:
            await send_reply(chat_id, "На сегодня задач нет 👍")
        return

    header = f"Фокус на {plan.date}"
    suffix_parts: list[str] = []
    if status_filter:
        suffix_parts.append(status_filter)
    if include_done:
        suffix_parts.append("all")
    if suffix_parts:
        header += " (" + ", ".join(suffix_parts) + ")"

    lines = [header]
    for item in items:
        emoji = STATUS_EMOJI.get(item.task.status, "•")
        lines.append(f"{item.rank}. {emoji} {item.task.title} ({item.score}🔸)")
    await send_reply(chat_id, "\n".join(lines))


async def _command_tasks(
    chat_id: int | None,
    db: Session,
    telegram_user: models.TelegramUser,
    args: Sequence[str],
) -> None:
    """
    /tasks [limit] [status] [#tag] [all]
    Примеры:
      /tasks
      /tasks 10
      /tasks planned
      /tasks #work
      /tasks 10 planned #work
      /tasks planned all
    """
    status, tag, limit, show_all = _parse_task_filters(args)
    limit = limit or 5

    stmt = (
        select(models.Task)
        .where(models.Task.user_id == telegram_user.id)
        .order_by(models.Task.created_at.desc())
    )
    if status:
        stmt = stmt.where(models.Task.status == status)
    if tag:
        stmt = stmt.where(models.Task.tags.contains([tag]))

    if not show_all:
        stmt = stmt.limit(limit)

    tasks = db.execute(stmt).scalars().all()
    if not tasks:
        await send_reply(chat_id, "Задач пока нет.")
        return

    head = "Последние задачи"
    filters: list[str] = []
    if status:
        filters.append(status)
    if tag:
        filters.append(f"#{tag}")
    if show_all:
        filters.append("all")
    if filters:
        head += f" ({', '.join(filters)})"

    lines = [head + ":"]
    for t in tasks:
        lines.append(f"- {_format_task_line(t)}")

    await send_reply(chat_id, "\n".join(lines))


async def _command_done(
    chat_id: int | None,
    db: Session,
    telegram_user: models.TelegramUser,
    args: Sequence[str],
) -> None:
    """
    /done <id> — отметить задачу пользователя выполненной.
    """
    if not args or not args[0].isdigit():
        await send_reply(chat_id, "Использование: /done <id>")
        return

    task_id = int(args[0])
    stmt = select(models.Task).where(
        models.Task.id == task_id,
        models.Task.user_id == telegram_user.id,
    ).limit(1)
    task = db.execute(stmt).scalars().first()

    if not task:
        await send_reply(chat_id, f"Задача с id {task_id} не найдена")
        return

    if task.status == TaskStatus.DONE.value:
        await send_reply(chat_id, "Эта задача уже в статусе done ✅")
        return

    change_task_status(task, TaskStatus.DONE)
    db.commit()
    db.refresh(task)

    await send_reply(chat_id=chat_id, text=f"Готово: {_format_task_line(task)}")


async def _command_status(
    chat_id: int | None,
    db: Session,
    telegram_user: models.TelegramUser,
    args: Sequence[str],
) -> None:
    """
    /status <id> <st> — изменить статус задачи (inbox|planned|done|snoozed).
    """
    if len(args) < 2 or not args[0].isdigit():
        await send_reply(chat_id, "Использование: /status <id> <inbox|planned|done|snoozed>")
        return

    task_id = int(args[0])
    new_status = _parse_status(args[1])

    if not new_status:
        await send_reply(
            chat_id,
            "Неизвестный статус. Используй: inbox | planned | done | snoozed",
        )
        return

    stmt = select(models.Task).where(
        models.Task.id == task_id,
        models.Task.user_id == telegram_user.id,
    ).limit(1)

    task = db.execute(stmt).scalars().first()

    if not task:
        await send_reply(chat_id, f"Задача с id {task_id} не найдена")
        return

    if task.status == new_status.value:
        await send_reply(chat_id, f"Статус уже {new_status.value}.")
        return

    change_task_status(task, new_status)
    db.commit()
    db.refresh(task)

    await send_reply(chat_id, f"Статус обновлён: {_format_task_line(task)}")


COMMAND_HANDLERS: dict[
    str,
    Callable[[int | None, Session, models.TelegramUser, Sequence[str]], Awaitable[None]],
] = {
    "/today": _command_today,
    "/focus": _command_today,
    "/tasks": _command_tasks,
    "/help": _command_help,
    "/start": _command_help,
    "/done": _command_done,
    "/status": _command_status,
}


async def try_handle_command(
    text: str,
    chat_id: int | None,
    db: Session,
    telegram_user: models.TelegramUser,
) -> bool:
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
        await handler(chat_id, db, telegram_user, args)
        return True

    if cmd.startswith("/"):
        await send_reply(chat_id, "Не знаю такую команду. Напиши /help")
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
