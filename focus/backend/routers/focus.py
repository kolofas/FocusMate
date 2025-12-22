# focus/backend/routers/focus.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from focus.backend.database.core import get_db
from ..schemas import PlanTodayResponse
from focus.backend.services.focus import get_plan_today

router = APIRouter()


@router.get("/today", response_model=PlanTodayResponse)
def read_today_plan(
    db: Session = Depends(get_db),
    user_id: int | None = Query(None, description="optional user id"),
) -> PlanTodayResponse:
    """
    Возвращает FocusList на сегодня.
    Если отсутствует — строит его (планировщик v0).
    """
    return get_plan_today(db, user_id=user_id, ensure_build=True)
