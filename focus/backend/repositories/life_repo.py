from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models


class LifeRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_categories(self, *, user_id: int | None) -> list[models.LifeCategory]:
        stmt = (
            select(models.LifeCategory)
            .where(
                models.LifeCategory.user_id.is_(None)
                if user_id is None
                else models.LifeCategory.user_id == user_id
            )
            .order_by(models.LifeCategory.sort_order.asc(), models.LifeCategory.id.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_action_templates(
        self,
        *,
        user_id: int | None,
        include_inactive: bool = False,
    ) -> list[models.ActionTemplate]:
        stmt = (
            select(models.ActionTemplate)
            .where(
                models.ActionTemplate.user_id.is_(None)
                if user_id is None
                else models.ActionTemplate.user_id == user_id
            )
            .order_by(models.ActionTemplate.id.asc())
        )
        if not include_inactive:
            stmt = stmt.where(models.ActionTemplate.is_active.is_(True))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def add_categories(self, categories: list[models.LifeCategory]) -> None:
        for category in categories:
            self.db.add(category)

    def add_action_templates(self, templates: list[models.ActionTemplate]) -> None:
        for template in templates:
            self.db.add(template)
