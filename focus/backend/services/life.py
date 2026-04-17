from __future__ import annotations

import re
from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models
from focus.backend.repositories.life_repo import LifeRepo
from focus.backend.schemas import UserActionCreate, UserActionLogResponse


_DEFAULT_CATEGORIES: list[tuple[str, str]] = [
    ("health", "Health"),
    ("work_money", "Work / Money"),
    ("growth_study", "Growth / Study"),
    ("energy_state", "Energy / State"),
    ("personal", "Personal"),
]

_DEFAULT_ACTION_TEMPLATES: list[tuple[str, str, int, int | None]] = [
    ("health", "Workout", 3, 30),
    ("health", "Walk", 2, 20),
    ("work_money", "30 min project work", 3, 30),
    ("growth_study", "Read / learn", 2, 20),
    ("energy_state", "Rest / reset", 2, 15),
    ("personal", "Quality time", 2, 30),
]


class LifeValidationError(ValueError):
    pass


class LifeNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class _ResolvedActionInput:
    template: models.ActionTemplate | None
    category_id: int
    title: str
    points: int
    duration_min: int | None


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower())
    return cleaned.strip("_")


async def _ensure_seeded(db: AsyncSession, *, user_id: int | None) -> None:
    repo = LifeRepo(db)
    existing_categories = await repo.list_categories(user_id=user_id)
    if existing_categories:
        return

    categories: list[models.LifeCategory] = []
    by_slug: dict[str, models.LifeCategory] = {}
    for idx, (slug, title) in enumerate(_DEFAULT_CATEGORIES):
        category = models.LifeCategory(
            user_id=user_id,
            slug=slug,
            title=title,
            sort_order=idx,
            is_active=True,
        )
        categories.append(category)
        by_slug[slug] = category

    repo.add_categories(categories)
    await db.flush()

    templates: list[models.ActionTemplate] = []
    for category_slug, title, points, duration in _DEFAULT_ACTION_TEMPLATES:
        category = by_slug[category_slug]
        templates.append(
            models.ActionTemplate(
                user_id=user_id,
                category_id=category.id,
                slug=_slugify(title),
                title=title,
                default_points=points,
                default_duration_min=duration,
                is_active=True,
            )
        )

    repo.add_action_templates(templates)
    await db.commit()


async def get_life_categories(
    db: AsyncSession, *, user_id: int | None
) -> list[models.LifeCategory]:
    await _ensure_seeded(db, user_id=user_id)
    repo = LifeRepo(db)
    return await repo.list_categories(user_id=user_id)


async def get_quick_action_templates(
    db: AsyncSession,
    *,
    user_id: int | None,
    include_inactive: bool = False,
) -> list[models.ActionTemplate]:
    await _ensure_seeded(db, user_id=user_id)
    repo = LifeRepo(db)
    return await repo.list_action_templates(
        user_id=user_id,
        include_inactive=include_inactive,
    )


async def _resolve_action_input(
    repo: LifeRepo,
    *,
    payload: UserActionCreate,
) -> _ResolvedActionInput:
    template: models.ActionTemplate | None = None
    title = payload.title
    category_id = payload.category_id
    points = payload.points if payload.points is not None else 1
    duration_min = payload.duration_min

    if payload.template_id is not None:
        template = await repo.get_action_template(
            template_id=payload.template_id,
            user_id=payload.user_id,
        )
        if template is None:
            raise LifeNotFoundError(
                f"Action template id={payload.template_id} not found"
            )

        if category_id is None:
            category_id = template.category_id
        if title is None:
            title = template.title
        if payload.points is None:
            points = template.default_points
        if duration_min is None:
            duration_min = template.default_duration_min

    if category_id is None:
        raise LifeValidationError("category_id is required")
    if not title:
        raise LifeValidationError("title is required")

    return _ResolvedActionInput(
        template=template,
        category_id=category_id,
        title=title,
        points=points,
        duration_min=duration_min,
    )


async def _ensure_category_exists(
    repo: LifeRepo,
    *,
    user_id: int | None,
    category_id: int,
) -> None:
    category = await repo.get_life_category(category_id=category_id, user_id=user_id)
    if category is None:
        raise LifeNotFoundError(f"Life category id={category_id} not found")


async def _compute_balance_after(
    repo: LifeRepo,
    *,
    user_id: int | None,
    category_id: int,
    delta_points: int,
) -> int:
    previous_balance = await repo.get_last_progress_balance(
        user_id=user_id,
        category_id=category_id,
    )
    return (previous_balance or 0) + delta_points


async def _persist_action_with_progress(
    db: AsyncSession,
    repo: LifeRepo,
    *,
    payload: UserActionCreate,
    resolved: _ResolvedActionInput,
    happened_at: datetime,
    balance_after: int,
) -> tuple[int, int]:
    action = models.UserAction(
        user_id=payload.user_id,
        template_id=resolved.template.id if resolved.template else payload.template_id,
        category_id=resolved.category_id,
        title=resolved.title,
        points=resolved.points,
        duration_min=resolved.duration_min,
        happened_at=happened_at,
    )
    repo.add_user_action(action)
    await db.flush()

    progress = models.ProgressEntry(
        user_id=payload.user_id,
        category_id=resolved.category_id,
        user_action_id=action.id,
        delta_points=resolved.points,
        balance_after=balance_after,
        occurred_at=happened_at,
    )
    repo.add_progress_entry(progress)
    await db.flush()
    await db.commit()

    return action.id, progress.id


async def log_user_action(
    db: AsyncSession,
    *,
    payload: UserActionCreate,
) -> UserActionLogResponse:
    await _ensure_seeded(db, user_id=payload.user_id)
    repo = LifeRepo(db)
    resolved = await _resolve_action_input(repo, payload=payload)
    await _ensure_category_exists(
        repo,
        user_id=payload.user_id,
        category_id=resolved.category_id,
    )
    balance_after = await _compute_balance_after(
        repo,
        user_id=payload.user_id,
        category_id=resolved.category_id,
        delta_points=resolved.points,
    )
    happened_at = payload.happened_at or datetime.now(timezone.utc)
    user_action_id, progress_entry_id = await _persist_action_with_progress(
        db,
        repo,
        payload=payload,
        resolved=resolved,
        happened_at=happened_at,
        balance_after=balance_after,
    )

    return UserActionLogResponse(
        user_action_id=user_action_id,
        progress_entry_id=progress_entry_id,
        category_id=resolved.category_id,
        delta_points=resolved.points,
    )
