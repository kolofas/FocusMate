from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Sequence, TypeAlias

from sqlalchemy.orm import Session

from focus.backend.database import models


@dataclass(frozen=True, slots=True)
class TelegramMeta:
    """Метаданные пользователя из Telegram update"""

    username: Optional[str] = None
    first_name: Optional[str] = None


@dataclass(frozen=True, slots=True)
class TelegramContext:
    """
    Контекст обработки Telegram-команды.
    Единая структура, чтобы не таскать 4-5 параметров по всему коду.
    """

    chat_id: Optional[int]
    db: Session
    telegram_user: models.TelegramUser
    meta: TelegramMeta | None = None


CommandHandler: TypeAlias = Callable[[TelegramContext, Sequence[str]], Awaitable[None]]
