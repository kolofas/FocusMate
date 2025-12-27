from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import models
from ..database.enums import TaskStatus
from ..repositories.planner_repo import PlannerRepo
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

    repo = PlannerRepo(db)

    focus_list = await repo.get_or_create_focus_list(target_date, user_id=user_id)
    candidates = await repo.list_candidates(user_id=user_id)

    ranked = sorted(candidates, key=_rank_key, reverse=True)[:limit]

    new_items = [
        models.FocusItem(
            focus_list_id=focus_list.id,
            task_id=task.id,
            rank=idx,
            score=score_task(task),
        )
        for idx, task in enumerate(ranked, start=1)
    ]

    await repo.replace_focus_items(focus_list_id=focus_list.id, items=new_items)

    return focus_list
