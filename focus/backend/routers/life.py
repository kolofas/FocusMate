from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database.core import get_db
from focus.backend.schemas import (
    LifeCategoryRead,
    ActionTemplateRead,
    UserActionCreate,
    UserActionLogResponse,
)
from focus.backend.services.life import (
    get_life_categories,
    get_quick_action_templates,
    log_user_action,
    LifeValidationError,
    LifeNotFoundError,
)

router = APIRouter()


@router.get("/categories", response_model=list[LifeCategoryRead])
async def read_life_categories(
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Query(None, description="optional user id"),
):
    return await get_life_categories(db, user_id=user_id)


@router.get("/actions/quick", response_model=list[ActionTemplateRead])
async def read_quick_action_templates(
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Query(None, description="optional user id"),
    include_inactive: bool = Query(False, description="include inactive templates"),
):
    return await get_quick_action_templates(
        db,
        user_id=user_id,
        include_inactive=include_inactive,
    )


@router.post("/actions/log", response_model=UserActionLogResponse)
async def create_user_action_log(
    payload: UserActionCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await log_user_action(db, payload=payload)
    except LifeValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LifeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
