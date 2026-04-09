"""add reminder fields to tasks

Revision ID: 7a8d6c3b2e1f
Revises: d6c677df315d
Create Date: 2026-04-09 12:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7a8d6c3b2e1f"
down_revision = "d6c677df315d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks", sa.Column("reminder_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "tasks",
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tasks_reminder_at", "tasks", ["reminder_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tasks_reminder_at", table_name="tasks")
    op.drop_column("tasks", "reminder_sent_at")
    op.drop_column("tasks", "reminder_at")
