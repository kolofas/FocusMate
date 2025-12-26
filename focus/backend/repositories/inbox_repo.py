from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models
from focus.backend.settings import settings


class InboxRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def exists_recent(
        self,
        *,
        source: str,
        dedup_key: str,
        window_minutes: int = settings.inbox_dedup_minutes,
        user_id: int | None = None,
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

        if user_id is not None:
            stmt = stmt.where(models.InboxEvent.user_id == user_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add(
        self,
        *,
        source: str,
        dedup_key: str,
        user_id: int | None = None,
    ) -> models.InboxEvent:
        """
        Сохраняет событие инбокса. Коммит не выполняется - чтобы участвовать в общей транзакции
        """
        event = models.InboxEvent(source=source, dedup=dedup_key)
        if user_id is not None:
            event.user_id = user_id

        self.db.add(event)
        await self.db.flush()
        return event
