from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models


async def get_user_task(
    db: AsyncSession, *, user_id: int, task_id: int
) -> models.Task | None:
    result = await db.execute(
        select(models.Task).where(
            models.Task.id == task_id,
            models.Task.user_id == user_id,
        )
    )
    return result.scalars().first()
