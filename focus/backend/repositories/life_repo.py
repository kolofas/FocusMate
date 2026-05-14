from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
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

    async def list_recent_user_actions(
        self, *, user_id: int | None, limit: int = 10
    ) -> list[tuple[models.UserAction, str | None, str | None]]:
        stmt = (
            select(
                models.UserAction,
                models.LifeCategory.slug.label("category_slug"),
                models.LifeCategory.title.label("category_title"),
            )
            .outerjoin(
                models.LifeCategory,
                models.LifeCategory.id == models.UserAction.category_id,
            )
            .where(
                models.UserAction.user_id.is_(None)
                if user_id is None
                else models.UserAction.user_id == user_id
            )
            .order_by(models.UserAction.happened_at.desc(), models.UserAction.id.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.all())

    async def get_user_action(
        self, *, action_id: int, user_id: int | None
    ) -> models.UserAction | None:
        stmt = select(models.UserAction).where(
            models.UserAction.id == action_id,
            models.UserAction.user_id.is_(None)
            if user_id is None
            else models.UserAction.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_latest_user_action(
        self, *, user_id: int | None
    ) -> models.UserAction | None:
        stmt = (
            select(models.UserAction)
            .where(
                models.UserAction.user_id.is_(None)
                if user_id is None
                else models.UserAction.user_id == user_id
            )
            .order_by(models.UserAction.happened_at.desc(), models.UserAction.id.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_latest_user_action_between(
        self,
        *,
        user_id: int | None,
        start_utc: datetime,
        end_utc: datetime,
    ) -> models.UserAction | None:
        stmt = (
            select(models.UserAction)
            .where(
                models.UserAction.happened_at >= start_utc,
                models.UserAction.happened_at < end_utc,
                models.UserAction.user_id.is_(None)
                if user_id is None
                else models.UserAction.user_id == user_id,
            )
            .order_by(models.UserAction.happened_at.desc(), models.UserAction.id.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def delete_progress_entries_by_action_id(
        self, *, action_id: int, user_id: int | None
    ) -> None:
        stmt = delete(models.ProgressEntry).where(
            models.ProgressEntry.user_action_id == action_id,
            models.ProgressEntry.user_id.is_(None)
            if user_id is None
            else models.ProgressEntry.user_id == user_id,
        )
        await self.db.execute(stmt)

    async def delete_user_action(
        self, *, action_id: int, user_id: int | None
    ) -> int:
        stmt = delete(models.UserAction).where(
            models.UserAction.id == action_id,
            models.UserAction.user_id.is_(None)
            if user_id is None
            else models.UserAction.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return int(result.rowcount or 0)

    async def sum_progress_points_by_category(
        self,
        *,
        user_id: int | None,
        start_utc: datetime,
        end_utc: datetime,
    ) -> dict[int, int]:
        stmt = (
            select(
                models.ProgressEntry.category_id,
                func.coalesce(func.sum(models.ProgressEntry.delta_points), 0).label(
                    "points"
                ),
            )
            .where(
                models.ProgressEntry.occurred_at >= start_utc,
                models.ProgressEntry.occurred_at < end_utc,
                models.ProgressEntry.category_id.is_not(None),
                models.ProgressEntry.user_id.is_(None)
                if user_id is None
                else models.ProgressEntry.user_id == user_id,
            )
            .group_by(models.ProgressEntry.category_id)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return {int(category_id): int(points) for category_id, points in rows}
