# backend/routers/inbox.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database.core import get_db
from focus.backend.schemas import InboxTelegram, TaskRead
from focus.backend.services.inbox import (
    accept_inbox_from_telegram,
    DuplicateInboxError,
)

router = APIRouter()


@router.post("/telegram", response_model=TaskRead, status_code=201)
async def accept_from_telegram(
    payload: InboxTelegram, db: AsyncSession = Depends(get_db)
):
    try:
        return await accept_inbox_from_telegram(db, payload)
    except DuplicateInboxError:
        raise HTTPException(409, "Duplicate inbox message")
