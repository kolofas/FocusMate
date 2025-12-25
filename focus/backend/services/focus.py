# focus/backend/services/focus.py
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import models
from focus.backend.schemas import PlanTodayResponse, PlanTodayResponseItem
from .planner import plan_today

__all__ = ["get_plan_today"]


def _base_stmt(today: date, user_id: int | None):
    return (
        select(models.FocusList)
        .options(
            selectinload(models.FocusList.items).selectinload(models.FocusItem.task)
        )
        .where(
            models.FocusList.date == today,
            models.FocusList.user_id.is_(None)
            if user_id is None
            else models.FocusList.user_id == user_id,
        )
        .limit(1)
    )


async def get_plan_today(
    db: AsyncSession,
    *,
    user_id: int | None,
    ensure_build: bool = True,
) -> PlanTodayResponse:
    today = date.today()

    stmt = _base_stmt(today, user_id)

    result = await db.execute(stmt)
    focus_list = result.scalars().first()

    if not focus_list and ensure_build:
        # строим и фиксируем
        await plan_today(db, user_id=user_id, for_date=today)

        # ВАЖНО: перечитываем уже с options(selectinload...)
        result = await db.execute(stmt)
        focus_list = result.scalars().first()

    items = [
        PlanTodayResponseItem(rank=it.rank, score=it.score, task=it.task)
        for it in (focus_list.items if focus_list else [])
    ]
    return PlanTodayResponse(date=today, items=items)
