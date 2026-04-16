"""add life categories and action templates

Revision ID: 8b12f3d4c5e6
Revises: 7a8d6c3b2e1f
Create Date: 2026-04-17 09:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8b12f3d4c5e6"
down_revision = "7a8d6c3b2e1f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "life_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["telegram_users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "slug", name="ux_life_categories_user_slug"),
    )
    op.create_index(
        "ix_life_categories_user_id", "life_categories", ["user_id"], unique=False
    )
    op.create_index("ix_life_categories_slug", "life_categories", ["slug"], unique=False)

    op.create_table(
        "action_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("default_points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("default_duration_min", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["life_categories.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["telegram_users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "slug", name="ux_action_templates_user_slug"),
    )
    op.create_index(
        "ix_action_templates_user_id", "action_templates", ["user_id"], unique=False
    )
    op.create_index(
        "ix_action_templates_category_id",
        "action_templates",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        "ix_action_templates_slug", "action_templates", ["slug"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_action_templates_slug", table_name="action_templates")
    op.drop_index("ix_action_templates_category_id", table_name="action_templates")
    op.drop_index("ix_action_templates_user_id", table_name="action_templates")
    op.drop_table("action_templates")

    op.drop_index("ix_life_categories_slug", table_name="life_categories")
    op.drop_index("ix_life_categories_user_id", table_name="life_categories")
    op.drop_table("life_categories")
