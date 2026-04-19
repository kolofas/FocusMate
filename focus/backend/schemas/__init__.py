from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date

from focus.backend.database.enums import TaskStatus


class AppBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(AppBaseModel):
    title: str
    description: Optional[str] = None
    source: Optional[str] = "manual"
    deadline: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    tags: List[str] = []


class TaskUpdate(AppBaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    tags: Optional[List[str]] = None


class TaskRead(AppBaseModel):
    id: int
    title: str
    description: Optional[str]
    source: str
    status: TaskStatus
    deadline: Optional[datetime]
    reminder_at: Optional[datetime] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime


class InboxTelegram(AppBaseModel):
    text: str
    chat_id: Optional[str] = None


class StatusChange(AppBaseModel):
    status: TaskStatus


class PlanTodayResponseItem(AppBaseModel):
    rank: int
    score: int
    task: TaskRead


class PlanTodayResponse(AppBaseModel):
    date: date
    items: List[PlanTodayResponseItem]


class LifeCategoryRead(AppBaseModel):
    id: int
    slug: str
    title: str
    sort_order: int
    is_active: bool


class ActionTemplateRead(AppBaseModel):
    id: int
    category_id: Optional[int]
    slug: str
    title: str
    default_points: int
    default_duration_min: Optional[int]
    is_active: bool


class UserActionCreate(AppBaseModel):
    user_id: int | None = None
    template_id: int | None = None
    category_id: int | None = None
    title: str | None = None
    points: int | None = None
    duration_min: int | None = None
    happened_at: datetime | None = None


class UserActionLogResponse(AppBaseModel):
    user_action_id: int
    progress_entry_id: int
    category_id: int | None
    delta_points: int


class UserActionRepeatCreate(AppBaseModel):
    user_action_id: int
    user_id: int | None = None
    happened_at: datetime | None = None


class UserActionRepeatResponse(UserActionLogResponse):
    repeated_from_action_id: int


class UserActionRepeatShortcutCreate(AppBaseModel):
    mode: str  # last | yesterday
    user_id: int | None = None
    happened_at: datetime | None = None
    reference_date: date | None = None


class UserActionRecentRead(AppBaseModel):
    id: int
    user_id: int | None
    template_id: int | None
    category_id: int | None
    category_slug: str | None
    category_title: str | None
    title: str
    points: int
    duration_min: int | None
    happened_at: datetime


class LifeDashboardCategoryPoints(AppBaseModel):
    category_id: int
    slug: str
    title: str
    points: int


class LifeDashboardTodayResponse(AppBaseModel):
    date: date
    total_points: int
    categories: List[LifeDashboardCategoryPoints]


class LifeDashboardWeekResponse(AppBaseModel):
    week_start: date
    week_end: date
    total_points: int
    categories: List[LifeDashboardCategoryPoints]
