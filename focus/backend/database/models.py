from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    func,
    UniqueConstraint,
    Index,
    ForeignKey,
    Date,
)
from sqlalchemy.dialects.postgresql import JSONB

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
