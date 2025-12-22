from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import models
from focus.backend.utils.normalize_text import normalize_text
from ..settings import settings


__all__ = ["make_dedup", "is_duplicate_inbox", "save_inbox_event"]


def make_dedup(text: str) -> str:
    """
    Возвращает стабильный dedup-ключ для исходного текста.
    Нормализуем пробелы и регистры, затем берем sha256 и сокращаем до 32 hex-символов.
    """
    norm = normalize_text(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:32]


def is_duplicate_inbox(
    db: Session,
    source: str,
    dedup_key: str,
    window_minutes: int = settings.inbox_dedup_minutes,
) -> bool:
    """
    Проверяет наличие события инбокса с тем же (source, dedup) за последнее окно времени.
    Коммит не выполняется — ответственность вызывающего.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    stmt = (
        select(models.InboxEvent.id)
        .where(
            models.InboxEvent.source == source,
            models.InboxEvent.dedup == dedup_key,
            models.InboxEvent.created_at >= since,
        )
        .limit(1)
    )
    return db.execute(stmt).first() is not None


def save_inbox_event(db: Session, source: str, dedup_key: str) -> models.InboxEvent:
    """
    Сохраняет событие инбокса. Коммит не выполняется - чтобы участвовать в общей транзакции
    """
    event = models.InboxEvent(source=source, dedup=dedup_key)
    db.add(event)
    return event
