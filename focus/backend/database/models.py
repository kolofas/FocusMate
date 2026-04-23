from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    func,
    UniqueConstraint,
    Index,
    ForeignKey,
    Date,
)
from sqlalchemy.dialects.postgresql import JSONB
from fastapi_users.db import SQLAlchemyBaseUserTable

Base = declarative_base()


def JSONType():
    return JSONB


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)  # index=True не нужен
    user_id = Column(
        Integer, ForeignKey("telegram_users.id", ondelete="SET NULL"), nullable=True
    )
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(
        String(30), nullable=False, default="manual"
    )  # manual|telegram|email
    status = Column(
        String(20), nullable=False, default="inbox"
    )  # inbox|planned|done|snoozed
    deadline = Column(DateTime(timezone=True), nullable=True)
    reminder_at = Column(DateTime(timezone=True), nullable=True)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSONType(), nullable=False, default=list)  # фабрика вместо []
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_deadline", "deadline"),
        Index("ix_tasks_reminder_at", "reminder_at"),
    )


class InboxEvent(Base):
    __tablename__ = "inbox_events"

    id = Column(Integer, primary_key=True)
    source = Column(String(20), nullable=False, default="telegram")
    dedup = Column(String(64), nullable=False, index=True)
    user_id = Column(
        Integer, ForeignKey("telegram_users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("source", "dedup", name="ux_source_dedup"),)


class FocusList(Base):
    __tablename__ = "focus_list"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    user_id = Column(Integer, nullable=True)  # оставляем под будущее

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items = relationship(
        "FocusItem",
        back_populates="focus_list",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("date", "user_id", name="ux_focus_lists_date_user"),
        Index("ix_focus_lists_date", "date"),
    )


class FocusItem(Base):
    __tablename__ = "focus_items"

    id = Column(Integer, primary_key=True)
    focus_list_id = Column(
        Integer,
        ForeignKey("focus_list.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id = Column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank = Column(Integer, nullable=False)  # 1..n (1 — самый высокий приоритет)
    score = Column(Integer, nullable=False)  # от планировщика

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    focus_list = relationship("FocusList", back_populates="items")
    task = relationship("Task", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "focus_list_id", "task_id", name="ux_focus_items_unique_task_per_list"
        ),
        Index("ix_focus_items_rank", "focus_list_id", "rank"),
    )


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String(50), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    screen_message_id = Column(Integer, nullable=True)


class WebUser(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "web_users"

    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(
        Integer, ForeignKey("telegram_users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_web_users_email"),
        UniqueConstraint("telegram_user_id", name="ux_web_users_telegram_user_id"),
        Index("ix_web_users_telegram_user_id", "telegram_user_id"),
    )


class LifeCategory(Base):
    __tablename__ = "life_categories"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("telegram_users.id", ondelete="SET NULL"), nullable=True
    )
    slug = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    templates = relationship(
        "ActionTemplate", back_populates="category", lazy="selectin"
    )
    progress_entries = relationship(
        "ProgressEntry", back_populates="category", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="ux_life_categories_user_slug"),
        Index("ix_life_categories_user_id", "user_id"),
        Index("ix_life_categories_slug", "slug"),
    )


class ActionTemplate(Base):
    __tablename__ = "action_templates"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("telegram_users.id", ondelete="SET NULL"), nullable=True
    )
    category_id = Column(
        Integer, ForeignKey("life_categories.id", ondelete="SET NULL"), nullable=True
    )
    slug = Column(String(80), nullable=False)
    title = Column(String(200), nullable=False)
    default_points = Column(Integer, nullable=False, default=1)
    default_duration_min = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    category = relationship("LifeCategory", back_populates="templates", lazy="selectin")
    user_actions = relationship(
        "UserAction", back_populates="template", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="ux_action_templates_user_slug"),
        Index("ix_action_templates_user_id", "user_id"),
        Index("ix_action_templates_category_id", "category_id"),
        Index("ix_action_templates_slug", "slug"),
    )


class UserAction(Base):
    __tablename__ = "user_actions"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("telegram_users.id", ondelete="SET NULL"), nullable=True
    )
    template_id = Column(
        Integer, ForeignKey("action_templates.id", ondelete="SET NULL"), nullable=True
    )
    category_id = Column(
        Integer, ForeignKey("life_categories.id", ondelete="SET NULL"), nullable=True
    )
    title = Column(String(200), nullable=False)
    points = Column(Integer, nullable=False, default=1)
    duration_min = Column(Integer, nullable=True)
    happened_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    template = relationship(
        "ActionTemplate", back_populates="user_actions", lazy="selectin"
    )
    progress_entries = relationship(
        "ProgressEntry",
        back_populates="user_action",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_user_actions_user_id", "user_id"),
        Index("ix_user_actions_template_id", "template_id"),
        Index("ix_user_actions_category_id", "category_id"),
        Index("ix_user_actions_happened_at", "happened_at"),
    )


class ProgressEntry(Base):
    __tablename__ = "progress_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("telegram_users.id", ondelete="SET NULL"), nullable=True
    )
    category_id = Column(
        Integer, ForeignKey("life_categories.id", ondelete="SET NULL"), nullable=True
    )
    user_action_id = Column(
        Integer, ForeignKey("user_actions.id", ondelete="SET NULL"), nullable=True
    )
    delta_points = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=True)
    occurred_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    category = relationship(
        "LifeCategory", back_populates="progress_entries", lazy="selectin"
    )
    user_action = relationship(
        "UserAction", back_populates="progress_entries", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_progress_entries_user_id", "user_id"),
        Index("ix_progress_entries_category_id", "category_id"),
        Index("ix_progress_entries_user_action_id", "user_action_id"),
        Index("ix_progress_entries_occurred_at", "occurred_at"),
    )
