# focus/backend/services/focus.py
from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.schemas import PlanTodayResponse, PlanTodayResponseItem
from .planner import plan_today

from ..repositories.focus_repo import FocusRepo

__all__ = ["get_plan_today"]


async def get_plan_today(
    db: AsyncSession,
    *,
    user_id: int | None,
    ensure_build: bool = True,
    force_rebuild: bool = False,
) -> PlanTodayResponse:
    today = date.today()

    repo = FocusRepo(db)

    focus_list = await repo.get_focus_list_with_items(today, user_id=user_id)

    if force_rebuild:
        await plan_today(db, user_id=user_id, for_date=today)
        await db.commit()
        focus_list = await repo.get_focus_list_with_items(today, user_id=user_id)
    elif not focus_list and ensure_build:
        await plan_today(db, user_id=user_id, for_date=today)
        await db.commit()
        focus_list = await repo.get_focus_list_with_items(today, user_id=user_id)

    items = [
        PlanTodayResponseItem(rank=it.rank, score=it.score, task=it.task)
        for it in (focus_list.items if focus_list else [])
    ]
    return PlanTodayResponse(date=today, items=items)
