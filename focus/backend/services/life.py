from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models
from focus.backend.repositories.life_repo import LifeRepo


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
                slug=title.lower().replace(" ", "_"),
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
