from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database.core import get_db
from focus.backend.schemas import (
    LifeCategoryRead,
    ActionTemplateRead,
    UserActionCreate,
    UserActionLogResponse,
    UserActionRepeatCreate,
    UserActionRepeatShortcutCreate,
    UserActionRepeatResponse,
    UserActionRecentRead,
    LifeDashboardTodayResponse,
    LifeDashboardWeekResponse,
)
from focus.backend.services.life import (
    delete_user_action,
    get_life_categories,
    get_quick_action_templates,
    log_user_action,
    repeat_user_action,
    repeat_user_action_shortcut,
    get_recent_user_actions,
    get_life_dashboard_today,
    get_life_dashboard_week,
    LifeValidationError,
    LifeNotFoundError,
)
from focus.backend.auth import current_active_user_optional, resolve_scope_user_id
from focus.backend.database import models

router = APIRouter()


@router.get("/categories", response_model=list[LifeCategoryRead])
async def read_life_categories(
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Query(None, description="optional user id"),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, user_id)
    return await get_life_categories(db, user_id=resolved_user_id)


@router.get("/actions/quick", response_model=list[ActionTemplateRead])
async def read_quick_action_templates(
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Query(None, description="optional user id"),
    include_inactive: bool = Query(False, description="include inactive templates"),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, user_id)
    return await get_quick_action_templates(
        db,
        user_id=resolved_user_id,
        include_inactive=include_inactive,
    )


@router.post("/actions/log", response_model=UserActionLogResponse)
async def create_user_action_log(
    payload: UserActionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, payload.user_id)
    payload = payload.model_copy(update={"user_id": resolved_user_id})
    try:
        return await log_user_action(db, payload=payload)
    except LifeValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LifeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/actions/repeat", response_model=UserActionRepeatResponse)
async def create_user_action_repeat(
    payload: UserActionRepeatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, payload.user_id)
    payload = payload.model_copy(update={"user_id": resolved_user_id})
    try:
        return await repeat_user_action(db, payload=payload)
    except LifeValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LifeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/actions/repeat-shortcut", response_model=UserActionRepeatResponse)
async def create_user_action_repeat_shortcut(
    payload: UserActionRepeatShortcutCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, payload.user_id)
    payload = payload.model_copy(update={"user_id": resolved_user_id})
    try:
        return await repeat_user_action_shortcut(db, payload=payload)
    except LifeValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LifeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/actions/recent", response_model=list[UserActionRecentRead])
async def read_recent_user_actions(
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Query(None, description="optional user id"),
    limit: int = Query(10, ge=1, le=100, description="max number of recent actions"),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, user_id)
    return await get_recent_user_actions(db, user_id=resolved_user_id, limit=limit)


@router.delete("/actions/{action_id}", status_code=204)
async def remove_user_action(
    action_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Query(None, description="optional user id"),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, user_id)
    try:
        await delete_user_action(
            db,
            user_id=resolved_user_id,
            action_id=action_id,
        )
    except LifeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/dashboard/today", response_model=LifeDashboardTodayResponse)
async def read_life_dashboard_today(
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Query(None, description="optional user id"),
    for_date: date | None = Query(None, description="override date YYYY-MM-DD"),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, user_id)
    return await get_life_dashboard_today(
        db, user_id=resolved_user_id, target_date=for_date
    )


@router.get("/dashboard/week", response_model=LifeDashboardWeekResponse)
async def read_life_dashboard_week(
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Query(None, description="optional user id"),
    for_date: date | None = Query(None, description="override date YYYY-MM-DD"),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, user_id)
    return await get_life_dashboard_week(
        db, user_id=resolved_user_id, target_date=for_date
    )
