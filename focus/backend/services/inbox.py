import logging
import hashlib
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models
from focus.backend.database.enums import TaskSource, TaskStatus
from focus.backend.repositories.inbox_repo import InboxRepo
from focus.backend.services.tasks import create_task_from_parsed
from focus.backend.schemas import InboxTelegram
from focus.backend.utils.normalize_text import normalize_text
from focus.backend.services.parsing import InboxParser

log = logging.getLogger(__name__)

_parser = InboxParser(tz=ZoneInfo("Europe/Amsterdam"))


def make_dedup(text: str) -> str:
    """
    Возвращает стабильный dedup-ключ для исходного текста.
    Нормализуем пробелы и регистры, затем берем sha256 и сокращаем до 32 hex-символов.
    """
    norm = normalize_text(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:32]


async def accept_inbox_from_telegram(
    db: AsyncSession,
    payload: InboxTelegram,
    *,
    user_id: int | None = None,
) -> models.Task:
    text = (payload.text or "").strip()
    if not text:
        raise ValueError("empty inbox message")

    source = TaskSource.TELEGRAM
    dedup_key = make_dedup(text)

    inbox_repo = InboxRepo(db)

    if await inbox_repo.exists_recent(
        source=source.value,
        dedup_key=dedup_key,
    ):
        raise DuplicateInboxError()

    parsed = _parser.parse(text)

    try:
        task = await create_task_from_parsed(
            db, parsed, source=source, status=TaskStatus.INBOX, raw_text=text
        )
        await inbox_repo.add(source=source.value, dedup_key=dedup_key, user_id=user_id)
        await db.commit()
        await db.refresh(task)
        return task
    except Exception:
        log.exception("Failed to accept inbox message")
        await db.rollback()
        raise


class DuplicateInboxError(Exception):
    pass
