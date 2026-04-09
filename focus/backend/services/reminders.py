from __future__ import annotations

from datetime import datetime, timezone
import logging
from zoneinfo import ZoneInfo

from sqlalchemy import select

from focus.backend.database import models
from focus.backend.database.core import SessionLocal
from focus.backend.services.telegram.api import send_reply
from focus.backend.settings import settings

log = logging.getLogger(__name__)


def _task_line(task: models.Task) -> str:
    return f"[id:{task.id}] {task.title}"


def _format_deadline_line(deadline: datetime | None) -> str:
    if not deadline:
        return ""
    try:
        tz = ZoneInfo(settings.app_timezone)
    except Exception:
        tz = ZoneInfo("UTC")
    local_dt = deadline.astimezone(tz)
    return f"\nДедлайн: {local_dt.strftime('%Y-%m-%d %H:%M')} ({settings.app_timezone})"


def _format_reminder_text(task: models.Task) -> str:
    return (
        "⏰ Напоминание\n"
        f"{_task_line(task)}"
        f"{_format_deadline_line(task.deadline)}"
    )


async def send_due_reminders_once(*, limit: int | None = None) -> int:
    """
    Отправляет due-напоминания и помечает их как отправленные.
    Возвращает количество успешно отправленных напоминаний.
    """
    now = datetime.now(timezone.utc)
    limit = limit or settings.reminders_batch_size
    sent = 0

    async with SessionLocal() as db:
        stmt = (
            select(models.Task, models.TelegramUser)
            .join(models.TelegramUser, models.Task.user_id == models.TelegramUser.id)
            .where(
                models.Task.reminder_at.is_not(None),
                models.Task.reminder_sent_at.is_(None),
                models.Task.reminder_at <= now,
            )
            .order_by(models.Task.reminder_at.asc(), models.Task.id.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            return 0

        for task, tg_user in rows:
            try:
                chat_id = int(tg_user.chat_id)
            except Exception:
                log.warning(
                    "Skip reminder: invalid chat_id user_id=%s chat_id=%s",
                    tg_user.id,
                    tg_user.chat_id,
                )
                continue

            msg_id = await send_reply(chat_id, _format_reminder_text(task))
            if msg_id is None:
                # временная ошибка сети/Telegram — пусть останется в очереди для retry
                continue

            task.reminder_sent_at = now
            sent += 1

        if sent:
            await db.commit()

    if sent:
        log.info("reminders.sent count=%s", sent)
    return sent
