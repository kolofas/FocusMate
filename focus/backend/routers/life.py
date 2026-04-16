from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database.core import get_db
from focus.backend.schemas import LifeCategoryRead, ActionTemplateRead
from focus.backend.services.life import get_life_categories, get_quick_action_templates

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
