"""add storage columns

Revision ID: 20260427_0002
Revises: 20260427_0001
Create Date: 2026-04-27 16:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260427_0002"
down_revision = "20260427_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("image_records")}

    if "storage_provider" not in columns:
        op.add_column("image_records", sa.Column("storage_provider", sa.String(length=20), nullable=True, server_default="local"))
        op.execute("UPDATE image_records SET storage_provider = 'local' WHERE storage_provider IS NULL")
        op.alter_column("image_records", "storage_provider", nullable=False, server_default=None)
    if "storage_bucket" not in columns:
        op.add_column("image_records", sa.Column("storage_bucket", sa.String(length=100), nullable=True))
    if "storage_object_key" not in columns:
        op.add_column("image_records", sa.Column("storage_object_key", sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("image_records")}

    if "storage_object_key" in columns:
        op.drop_column("image_records", "storage_object_key")
    if "storage_bucket" in columns:
        op.drop_column("image_records", "storage_bucket")
    if "storage_provider" in columns:
        op.drop_column("image_records", "storage_provider")
