# focus/backend/focus.py
from __future__ import annotations

from datetime import date
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import models
from focus.backend.schemas import PlanTodayResponse, PlanTodayResponseItem
from .planner import plan_today

__all__ = ["get_plan_today"]


def get_plan_today(
    db: Session,
    *,
    user_id: int | None,
    ensure_build: bool = True,
) -> PlanTodayResponse:
    """
    Возвращает план на сегодня. Если его нет и ensure_build=True — строит и фиксирует.
    """
    today = date.today()

    stmt = (
        select(models.FocusList)
        .where(
            models.FocusList.date == today,
            models.FocusList.user_id.is_(user_id) if user_id is None else models.FocusList.user_id == user_id,
        )
        .limit(1)
    )
    focus_list = db.execute(stmt).scalars().first()

    if not focus_list and ensure_build:
        focus_list = plan_today(db, user_id=user_id, for_date=today)

    items = [
        PlanTodayResponseItem(
            rank=it.rank,
            score=it.score,
            task=it.task,
        )
        for it in (focus_list.items if focus_list else [])
    ]
    return PlanTodayResponse(date=today, items=items)
