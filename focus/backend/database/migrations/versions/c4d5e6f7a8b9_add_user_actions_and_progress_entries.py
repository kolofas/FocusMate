"""add user actions and progress entries

Revision ID: c4d5e6f7a8b9
Revises: 8b12f3d4c5e6
Create Date: 2026-04-17 09:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c4d5e6f7a8b9"
down_revision = "8b12f3d4c5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column(
            "happened_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["telegram_users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["action_templates.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["life_categories.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_actions_user_id", "user_actions", ["user_id"], unique=False)
    op.create_index(
        "ix_user_actions_template_id", "user_actions", ["template_id"], unique=False
    )
    op.create_index(
        "ix_user_actions_category_id", "user_actions", ["category_id"], unique=False
    )
    op.create_index(
        "ix_user_actions_happened_at", "user_actions", ["happened_at"], unique=False
    )

    op.create_table(
        "progress_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("user_action_id", sa.Integer(), nullable=True),
        sa.Column("delta_points", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["telegram_users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["life_categories.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_action_id"],
            ["user_actions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_progress_entries_user_id", "progress_entries", ["user_id"], unique=False
    )
    op.create_index(
        "ix_progress_entries_category_id",
        "progress_entries",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        "ix_progress_entries_user_action_id",
        "progress_entries",
        ["user_action_id"],
        unique=False,
    )
    op.create_index(
        "ix_progress_entries_occurred_at",
        "progress_entries",
        ["occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_progress_entries_occurred_at", table_name="progress_entries")
    op.drop_index("ix_progress_entries_user_action_id", table_name="progress_entries")
    op.drop_index("ix_progress_entries_category_id", table_name="progress_entries")
    op.drop_index("ix_progress_entries_user_id", table_name="progress_entries")
    op.drop_table("progress_entries")

    op.drop_index("ix_user_actions_happened_at", table_name="user_actions")
    op.drop_index("ix_user_actions_category_id", table_name="user_actions")
    op.drop_index("ix_user_actions_template_id", table_name="user_actions")
    op.drop_index("ix_user_actions_user_id", table_name="user_actions")
    op.drop_table("user_actions")
