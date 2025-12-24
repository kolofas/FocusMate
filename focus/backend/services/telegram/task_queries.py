from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from focus.backend.database import models


def get_user_task(db: Session, *, user_id: int, task_id: int) -> models.Task | None:
    return (
        db.execute(
            select(models.Task).where(
                models.Task.id == task_id,
                models.Task.user_id == user_id,
            )
        )
        .scalars()
        .first()
    )
