from __future__ import annotations

from datetime import date
from typing import Optional, cast

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from focus.backend.database import models
from focus.backend.database.enums import TaskStatus


class PlannerRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_focus_list(
        self,
        target_date: date,
        *,
        user_id: Optional[int],
    ) -> models.FocusList:
        stmt = (
            select(models.FocusList)
            .options(selectinload(models.FocusList.items))
            .where(
                models.FocusList.date == target_date,
                models.FocusList.user_id.is_(None)
                if user_id is None
                else models.FocusList.user_id == user_id,
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        obj = result.scalars().first()
        if obj:
            return obj

        obj = models.FocusList(date=target_date, user_id=user_id)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def list_candidates(self, *, user_id: Optional[int]) -> list[models.Task]:
        stmt = select(models.Task).where(
            models.Task.status.in_([TaskStatus.INBOX.value, TaskStatus.PLANNED.value])
        )
        if user_id is None:
            stmt = stmt.where(models.Task.user_id.is_(None))
        else:
            stmt = stmt.where(models.Task.user_id == user_id)

        result = await self.db.execute(stmt)
        return cast(list[models.Task], result.scalars().all())

    async def replace_focus_items(
        self,
        *,
        focus_list_id: int,
        items: list[models.FocusItem],
    ) -> None:
        await self.db.execute(
            delete(models.FocusItem).where(
                models.FocusItem.focus_list_id == focus_list_id
            )
        )
        if items:
            self.db.add_all(items)
        await self.db.flush()
