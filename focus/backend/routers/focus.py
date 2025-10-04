# focus/backend/routers/focus.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from focus.backend.database.core import get_db
from ..schemas import PlanTodayResponse
from focus.backend.services.focus import get_plan_today

router = APIRouter()


@router.get("/today", response_model=PlanTodayResponse)
def read_today_plan(db: Session = Depends(get_db)) -> PlanTodayResponse:
    """
    Возвращает FocusList на сегодня.
    Если отсутствует — строит его (планировщик v0).
    """
    return get_plan_today(db, ensure_build=True)
