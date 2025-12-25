from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import models


async def _find_telegram_user(
    db: AsyncSession, chat_id: int
) -> Optional[models.TelegramUser]:
    stmt = (
        select(models.TelegramUser)
        .where(models.TelegramUser.chat_id == str(chat_id))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def _apply_profile_updates(
    user: models.TelegramUser,
    *,
    username: Optional[str],
    first_name: Optional[str],
) -> bool:
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


async def get_or_create_telegram_user(
    db: AsyncSession,
    chat_id: int,
    username: Optional[str],
    first_name: Optional[str],
) -> models.TelegramUser:
    """
    Получить пользователя по chat_id.
    Если не найден — создать.
    Если найден и пришли новые поля — обновить.
    """
    user = await _find_telegram_user(db, chat_id)
    if user:
        if await _apply_profile_updates(user, username=username, first_name=first_name):
            await db.flush()
        return user

    user = models.TelegramUser(
        chat_id=str(chat_id),
        username=username,
        first_name=first_name,
    )
    db.add(user)
    await db.flush()
    return user
