# focus/backend/planner.py
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import models
from ..database.enums import TaskStatus
from ..settings import settings

__all__ = ["score_task", "plan_today"]


def score_task(task: models.Task) -> int:
    """
    Правила v0:
      +30 — если в тегах есть 'urgent'
      дедлайн:
        просрочка          → +40
        ≤ 1 дня            → +30
        ≤ 3 дней           → +20
        ≤ 7 дней           → +10
        дальше/нет         → +0
      +10 — если status == planned
    """
    score = 0

    tags = {t.lower() for t in (task.tags or [])}
    if settings.urgent_tag in tags:
        score += 30

    score += _deadline_score(task.deadline)

    if task.status == TaskStatus.PLANNED.value:
        score += 10

    return score


def _as_aware_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        # считаем, что naive уже в UTC (для SQLite это частый кейс)
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _deadline_score(deadline: datetime | None) -> int:
    deadline = _as_aware_utc(deadline)  # ← приводим к aware UTC
    if not deadline:
        return 0

    now = datetime.now(timezone.utc)
    delta_seconds = (deadline - now).total_seconds()

    if delta_seconds <= 0:
        return 40  # просрочено
    days = delta_seconds / 86400.0
    if days <= 1:
        return 30
    if days <= 3:
        return 20
    if days <= 7:
        return 10
    return 0


def _get_or_create_focus_list(
        db: Session,
        target_date: date,
        *,
        user_id: Optional[int],
) -> models.FocusList:
    stmt = (
        select(models.FocusList)
        .where(
            models.FocusList.date == target_date,
            models.FocusList.user_id.is_(user_id) if user_id is None else models.FocusList.user_id == user_id,
        )
        .limit(1)
    )
    obj = db.execute(stmt).scalars().first()
    if obj:
        return obj

    obj = models.FocusList(date=target_date, user_id=user_id)
    db.add(obj)
    db.flush()
    return obj


def _select_candidates(db: Session, *, user_id: Optional[int]) -> list[models.Task]:
    """
    Берём только задачи этого пользователя.
    Для системных/ручных без пользователя — user_id IS NULL.
    """
    stmt = select(models.Task).where(
        models.Task.status.in_([TaskStatus.INBOX.value, TaskStatus.PLANNED.value])
    )
    if user_id is None:
        stmt = stmt.where(models.Task.user_id.is_(None))
    else:
        stmt = stmt.where(models.Task.user_id == user_id)
    return db.execute(stmt).scalars().all()


def _rank_key(task: models.Task):
    """
    Сортировка: по убыванию score, затем по возрастанию deadline, затем по возрастанию created_at.
    Реализовано через reverse=True и отрицательные timestamp для дат.
    """
    s = score_task(task)
    dl = task.deadline or datetime.max.replace(tzinfo=timezone.utc)
    ca = task.created_at or datetime.max.replace(tzinfo=timezone.utc)
    return (s, -dl.timestamp(), -ca.timestamp())


def plan_today(
    db: Session,
    *,
    user_id: Optional[int],
    limit: Optional[int] = None,
    for_date: Optional[date] = None,
) -> models.FocusList:
    """
    Строит/обновляет фокус-лист НА ПОЛЬЗОВАТЕЛЯ.
    """
    target_date = for_date or date.today()
    limit = limit or settings.focus_limit

    focus_list = _get_or_create_focus_list(db, target_date, user_id=user_id)
    candidates = _select_candidates(db, user_id=user_id)
    ranked = sorted(candidates, key=_rank_key, reverse=True)[:limit]

    focus_list.items.clear()
    for idx, task in enumerate(ranked, start=1):
        focus_list.items.append(
            models.FocusItem(task=task, rank=idx, score=score_task(task))
        )

    db.flush()
    return focus_list