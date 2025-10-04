from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Text, DateTime, func, UniqueConstraint, Index, ForeignKey, Date
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

def JSONType():
    # JSONB в PG, JSON в SQLite
    return JSONB().with_variant(SQLITE_JSON, "sqlite")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)  # index=True не нужен
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(30), nullable=False, default="manual")  # manual|telegram|email
    status = Column(String(20), nullable=False, default="inbox")   # inbox|planned|done|snoozed
    deadline = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSONType(), nullable=False, default=list)        # фабрика вместо []
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_deadline", "deadline"),
    )

class InboxEvent(Base):
    __tablename__ = "inbox_events"

    id = Column(Integer, primary_key=True)
    source = Column(String(20), nullable=False, default="telegram")
    dedup = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("source", "dedup", name="ux_source_dedup"),)

class FocusList(Base):
    __tablename__ = "focus_list"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    user_id = Column(Integer, nullable=True)  # оставляем под будущее

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    items = relationship("FocusItem", back_populates="focus_list", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("date", "user_id", name="ux_focus_lists_date_user"),  # <-- исправлено
        Index("ix_focus_lists_date", "date"),                                  # <-- исправлено
    )

class FocusItem(Base):
    __tablename__ = "focus_items"

    id = Column(Integer, primary_key=True)
    focus_list_id = Column(Integer, ForeignKey("focus_list.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    rank = Column(Integer, nullable=False)   # 1..n (1 — самый высокий приоритет)
    score = Column(Integer, nullable=False)  # от планировщика

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    focus_list = relationship("FocusList", back_populates="items")
    task = relationship("Task")

    __table_args__ = (
        UniqueConstraint("focus_list_id", "task_id", name="ux_focus_items_unique_task_per_list"),
        Index("ix_focus_items_rank", "focus_list_id", "rank"),
    )
