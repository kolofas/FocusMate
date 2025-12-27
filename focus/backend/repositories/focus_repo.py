from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from focus.backend.database import models


class FocusRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_focus_list_with_items(
        self,
        target_date: date,
        *,
        user_id: Optional[int],
    ) -> models.FocusList | None:
        stmt = (
            select(models.FocusList)
            .options(
                selectinload(models.FocusList.items).selectinload(models.FocusItem.task)
            )
            .where(
                models.FocusList.date == target_date,
                models.FocusList.user_id.is_(None)
                if user_id is None
                else models.FocusList.user_id == user_id,
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
