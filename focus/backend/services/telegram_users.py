from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import models


def _find_telegram_user(db: Session, chat_id: int) -> Optional[models.TelegramUser]:
    stmt = (
        select(models.TelegramUser).where(models.TelegramUser.chat_id == str(chat_id)).limit(1)
    )
    return db.execute(stmt).scalars().first()


def _apply_profile_updates(user: models.TelegramUser, *, username: Optional[str], first_name: Optional[str],) -> bool:
    """
    Применяет обновления к профилю.
    Возвращает True, если были изменения
    """
    changed = False

    if username and user.username != username:
        user.username = username
        changed = True

    if first_name and user.first_name != first_name:
        user.first_name = first_name
        changed = True

    return changed


def get_or_create_telegram_user(
        db: Session,
        chat_id: int,
        username: Optional[str],
        first_name: Optional[str],
) -> models.TelegramUser:
    """
    Получить пользователя по chat_id.
    Если не найден — создать.
    Если найден и пришли новые поля — обновить.
    """
    user = _find_telegram_user(db, chat_id)
    if user:
        if _apply_profile_updates(user, username=username, first_name=first_name):
            db.flush()
        return user

    user = models.TelegramUser(
        chat_id=str(chat_id),
        username=username,
        first_name=first_name,
    )
    db.add(user)
    db.flush()
    return user




