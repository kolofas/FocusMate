# focus/backend/planner.py
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional, Any, Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


async def _get_or_create_focus_list(
    db: AsyncSession,
    target_date: date,
    *,
    user_id: Optional[int],
) -> models.FocusList:
    stmt = (
        select(models.FocusList)
        .options(selectinload(models.FocusList.items))
        .where(
            models.FocusList.date == target_date,
            models.FocusList.user_id.is_(user_id)
            if user_id is None
            else models.FocusList.user_id == user_id,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    obj = result.scalars().first()
    if obj:
        return obj

    obj = models.FocusList(date=target_date, user_id=user_id)
    db.add(obj)
    await db.flush()
    return obj


async def _select_candidates(
    db: AsyncSession, *, user_id: Optional[int]
) -> Sequence[Any]:
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

    result = await db.execute(stmt)
    return result.scalars().all()


def _rank_key(task: models.Task):
    """
    Сортировка: по убыванию score, затем по возрастанию deadline, затем по возрастанию created_at.
    Реализовано через reverse=True и отрицательные timestamp для дат.
    """
    s = score_task(task)
    dl = task.deadline or datetime.max.replace(tzinfo=timezone.utc)
    ca = task.created_at or datetime.max.replace(tzinfo=timezone.utc)
    return (s, -dl.timestamp(), -ca.timestamp())


async def plan_today(
    db: AsyncSession,
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

    focus_list = await _get_or_create_focus_list(db, target_date, user_id=user_id)
    candidates = await _select_candidates(db, user_id=user_id)
    ranked = sorted(candidates, key=_rank_key, reverse=True)[:limit]

    # 1) очистка через SQL, НЕ через relationship
    await db.execute(
        delete(models.FocusItem).where(models.FocusItem.focus_list_id == focus_list.id)
    )

    # 2) вставка новых items (тоже без трогания focus_list.items)
    new_items = [
        models.FocusItem(
            focus_list_id=focus_list.id,
            task_id=task.id,
            rank=idx,
            score=score_task(task),
        )
        for idx, task in enumerate(ranked, start=1)
    ]
    db.add_all(new_items)

    await db.flush()
    return focus_list
