"""add users table

Revision ID: 20260515_0009
Revises: 20260507_0008
Create Date: 2026-05-15 10:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260515_0009"
down_revision = "20260507_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("username", sa.String(length=100), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=30), nullable=False),
            sa.Column("display_name", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("user_id"),
            sa.UniqueConstraint("username"),
        )
        op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
