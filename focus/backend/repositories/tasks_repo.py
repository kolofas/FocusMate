from typing import cast

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models
from focus.backend.schemas.task_queries import TaskListQuery


class TaskRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_tasks(self, query: TaskListQuery) -> list[models.Task]:
        q = query.normalized()

        stmt = select(models.Task)

        if q.user_id is None:
            stmt = stmt.where(models.Task.user_id.is_(None))
        else:
            stmt = stmt.where(models.Task.user_id == q.user_id)

        if q.tag:
            stmt = stmt.where(models.Task.tags.contains([q.tag]))

        if q.status:
            stmt = stmt.where(models.Task.status == q.status)

        if q.q:
            stmt = stmt.where(func.lower(models.Task.title).like(f"%{q.q.lower()}%"))

        column = getattr(models.Task, q.order_by)
        stmt = stmt.order_by(asc(column) if q.direction == "asc" else desc(column))

        stmt = stmt.limit(q.limit).offset(q.offset)

        result = await self.db.execute(stmt)
        return cast(list[models.Task], result.scalars().all())
