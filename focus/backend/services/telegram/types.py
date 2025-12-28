from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Sequence, TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models


@dataclass(frozen=True, slots=True)
class TelegramMeta:
    """Метаданные пользователя из Telegram update"""

    username: str | None = None
    first_name: str | None = None


@dataclass(frozen=True, slots=True)
class TelegramContext:
    """
    Контекст обработки Telegram-команды.
    Единая структура, чтобы не таскать 4-5 параметров по всему коду.
    """

    chat_id: int
    db: AsyncSession
    telegram_user: models.TelegramUser
    meta: TelegramMeta | None = None


CommandHandler: TypeAlias = Callable[[TelegramContext, Sequence[str]], Awaitable[None]]
