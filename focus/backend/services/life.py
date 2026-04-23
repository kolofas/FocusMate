from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from focus.backend.database import models
from focus.backend.repositories.life_repo import LifeRepo
from focus.backend.schemas import (
    LifeDashboardCategoryPoints,
    LifeDashboardTodayResponse,
    LifeDashboardWeekResponse,
    UserActionCreate,
    UserActionLogResponse,
    UserActionRepeatCreate,
    UserActionRepeatShortcutCreate,
    UserActionRepeatResponse,
    UserActionRecentRead,
)
from focus.backend.settings import settings


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


def _resolve_app_tz() -> ZoneInfo:
    try:
        return ZoneInfo(settings.app_timezone)
    except Exception:
        return ZoneInfo("UTC")


def _local_day_bounds_utc(target_date: date) -> tuple[datetime, datetime]:
    tz = _resolve_app_tz()
    start_local = datetime.combine(target_date, time.min).replace(tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _local_week_bounds_utc(target_date: date) -> tuple[datetime, datetime]:
    week_start = target_date - timedelta(days=target_date.weekday())
    week_end_exclusive = week_start + timedelta(days=7)
    start_utc, _ = _local_day_bounds_utc(week_start)
    end_utc, _ = _local_day_bounds_utc(week_end_exclusive)
    return start_utc, end_utc


def _local_yesterday_bounds_utc(
    target_date: date | None = None,
) -> tuple[datetime, datetime]:
    base_day = target_date or datetime.now(_resolve_app_tz()).date()
    yesterday = base_day - timedelta(days=1)
    return _local_day_bounds_utc(yesterday)


def _build_dashboard_categories(
    *,
    categories: list[models.LifeCategory],
    points_by_category: dict[int, int],
) -> list[LifeDashboardCategoryPoints]:
    return [
        LifeDashboardCategoryPoints(
            category_id=category.id,
            slug=category.slug,
            title=category.title,
            points=points_by_category.get(category.id, 0),
        )
        for category in categories
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

    try:
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
    except IntegrityError:
        # Race-safe seeding: a concurrent request may create the same defaults first.
        await db.rollback()
        existing_categories = await repo.list_categories(user_id=user_id)
        if existing_categories:
            return
        raise


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


async def get_recent_user_actions(
    db: AsyncSession,
    *,
    user_id: int | None,
    limit: int = 10,
) -> list[UserActionRecentRead]:
    repo = LifeRepo(db)
    recent_rows = await repo.list_recent_user_actions(user_id=user_id, limit=limit)
    return [
        UserActionRecentRead(
            id=user_action.id,
            user_id=user_action.user_id,
            template_id=user_action.template_id,
            category_id=user_action.category_id,
            category_slug=category_slug,
            category_title=category_title,
            title=user_action.title,
            points=user_action.points,
            duration_min=user_action.duration_min,
            happened_at=user_action.happened_at,
        )
        for user_action, category_slug, category_title in recent_rows
    ]


async def repeat_user_action(
    db: AsyncSession,
    *,
    payload: UserActionRepeatCreate,
) -> UserActionRepeatResponse:
    await _ensure_seeded(db, user_id=payload.user_id)
    repo = LifeRepo(db)
    source = await repo.get_user_action(
        action_id=payload.user_action_id,
        user_id=payload.user_id,
    )
    if source is None:
        raise LifeNotFoundError(f"User action id={payload.user_action_id} not found")
    if source.category_id is None:
        raise LifeValidationError("Source action has no category_id")

    await _ensure_category_exists(
        repo,
        user_id=payload.user_id,
        category_id=source.category_id,
    )
    balance_after = await _compute_balance_after(
        repo,
        user_id=payload.user_id,
        category_id=source.category_id,
        delta_points=source.points,
    )
    happened_at = payload.happened_at or datetime.now(timezone.utc)
    repeat_payload = UserActionCreate(
        user_id=payload.user_id,
        template_id=source.template_id,
        category_id=source.category_id,
        title=source.title,
        points=source.points,
        duration_min=source.duration_min,
        happened_at=happened_at,
    )
    resolved = _ResolvedActionInput(
        template=None,
        category_id=source.category_id,
        title=source.title,
        points=source.points,
        duration_min=source.duration_min,
    )
    user_action_id, progress_entry_id = await _persist_action_with_progress(
        db,
        repo,
        payload=repeat_payload,
        resolved=resolved,
        happened_at=happened_at,
        balance_after=balance_after,
    )
    return UserActionRepeatResponse(
        user_action_id=user_action_id,
        progress_entry_id=progress_entry_id,
        category_id=source.category_id,
        delta_points=source.points,
        repeated_from_action_id=source.id,
    )


async def repeat_user_action_shortcut(
    db: AsyncSession,
    *,
    payload: UserActionRepeatShortcutCreate,
) -> UserActionRepeatResponse:
    await _ensure_seeded(db, user_id=payload.user_id)
    repo = LifeRepo(db)

    if payload.mode == "last":
        source = await repo.get_latest_user_action(user_id=payload.user_id)
    elif payload.mode == "yesterday":
        start_utc, end_utc = _local_yesterday_bounds_utc(payload.reference_date)
        source = await repo.get_latest_user_action_between(
            user_id=payload.user_id,
            start_utc=start_utc,
            end_utc=end_utc,
        )
    else:
        raise LifeValidationError("mode must be one of: last, yesterday")

    if source is None:
        raise LifeNotFoundError(f"No source action found for mode={payload.mode}")

    return await repeat_user_action(
        db,
        payload=UserActionRepeatCreate(
            user_action_id=source.id,
            user_id=payload.user_id,
            happened_at=payload.happened_at,
        ),
    )


async def get_life_dashboard_today(
    db: AsyncSession,
    *,
    user_id: int | None,
    target_date: date | None = None,
) -> LifeDashboardTodayResponse:
    day = target_date or datetime.now(_resolve_app_tz()).date()
    await _ensure_seeded(db, user_id=user_id)
    repo = LifeRepo(db)
    categories = await repo.list_categories(user_id=user_id)
    start_utc, end_utc = _local_day_bounds_utc(day)
    points_by_category = await repo.sum_progress_points_by_category(
        user_id=user_id,
        start_utc=start_utc,
        end_utc=end_utc,
    )
    category_points = _build_dashboard_categories(
        categories=categories, points_by_category=points_by_category
    )
    return LifeDashboardTodayResponse(
        date=day,
        total_points=sum(item.points for item in category_points),
        categories=category_points,
    )


async def get_life_dashboard_week(
    db: AsyncSession,
    *,
    user_id: int | None,
    target_date: date | None = None,
) -> LifeDashboardWeekResponse:
    day = target_date or datetime.now(_resolve_app_tz()).date()
    week_start = day - timedelta(days=day.weekday())
    week_end = week_start + timedelta(days=6)
    await _ensure_seeded(db, user_id=user_id)
    repo = LifeRepo(db)
    categories = await repo.list_categories(user_id=user_id)
    start_utc, end_utc = _local_week_bounds_utc(day)
    points_by_category = await repo.sum_progress_points_by_category(
        user_id=user_id,
        start_utc=start_utc,
        end_utc=end_utc,
    )
    category_points = _build_dashboard_categories(
        categories=categories, points_by_category=points_by_category
    )
    return LifeDashboardWeekResponse(
        week_start=week_start,
        week_end=week_end,
        total_points=sum(item.points for item in category_points),
        categories=category_points,
    )
