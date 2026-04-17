from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models


class LifeRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_categories(
        self, *, user_id: int | None
    ) -> list[models.LifeCategory]:
        stmt = (
            select(models.LifeCategory)
            .where(
                models.LifeCategory.user_id.is_(None)
                if user_id is None
                else models.LifeCategory.user_id == user_id
            )
            .order_by(
                models.LifeCategory.sort_order.asc(), models.LifeCategory.id.asc()
            )
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

    async def get_action_template(
        self, *, template_id: int, user_id: int | None
    ) -> models.ActionTemplate | None:
        stmt = select(models.ActionTemplate).where(
            models.ActionTemplate.id == template_id,
            models.ActionTemplate.user_id.is_(None)
            if user_id is None
            else models.ActionTemplate.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_life_category(
        self, *, category_id: int, user_id: int | None
    ) -> models.LifeCategory | None:
        stmt = select(models.LifeCategory).where(
            models.LifeCategory.id == category_id,
            models.LifeCategory.user_id.is_(None)
            if user_id is None
            else models.LifeCategory.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_last_progress_balance(
        self, *, user_id: int | None, category_id: int
    ) -> int | None:
        stmt = (
            select(models.ProgressEntry.balance_after)
            .where(
                models.ProgressEntry.category_id == category_id,
                models.ProgressEntry.user_id.is_(None)
                if user_id is None
                else models.ProgressEntry.user_id == user_id,
            )
            .order_by(
                models.ProgressEntry.occurred_at.desc(),
                models.ProgressEntry.id.desc(),
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def add_user_action(self, action: models.UserAction) -> None:
        self.db.add(action)

    def add_progress_entry(self, entry: models.ProgressEntry) -> None:
        self.db.add(entry)
