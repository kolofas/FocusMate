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


def get_plan_today(db: Session, *, ensure_build: bool = True) -> PlanTodayResponse:
    """
    Возвращает план на сегодня. Если его нет и ensure_build=True — строит и фиксирует.
    """
    today = date.today()

    stmt = select(models.FocusList).where(models.FocusList.date == today).limit(1)
    focus_list = db.execute(stmt).scalars().first()

    if focus_list is None and ensure_build:
        focus_list = plan_today(db, for_date=today)
        db.commit()
        db.refresh(focus_list)

    if focus_list is None:
        return PlanTodayResponse(date=today, items=[])

    items: List[PlanTodayResponseItem] = [
        PlanTodayResponseItem(rank=it.rank, score=it.score, task=it.task)
        for it in sorted(focus_list.items, key=lambda x: x.rank)
    ]
    return PlanTodayResponse(date=today, items=items)
