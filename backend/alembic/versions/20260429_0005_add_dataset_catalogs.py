"""add dataset catalogs

Revision ID: 20260429_0005
Revises: 20260429_0004
Create Date: 2026-04-29 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_0005"
down_revision = "20260429_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("dataset_catalogs"):
        op.create_table(
            "dataset_catalogs",
            sa.Column("dataset_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("source_name", sa.String(length=120), nullable=False),
            sa.Column("homepage_url", sa.String(length=500), nullable=False),
            sa.Column("paper_url", sa.String(length=500), nullable=True),
            sa.Column("license", sa.String(length=120), nullable=True),
            sa.Column("image_type", sa.String(length=40), nullable=False, server_default="panoramic"),
            sa.Column("task_types", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("disease_tags", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("sample_size", sa.String(length=120), nullable=True),
            sa.Column("annotation_format", sa.String(length=160), nullable=True),
            sa.Column("access_status", sa.String(length=40), nullable=False, server_default="open"),
            sa.Column("priority", sa.String(length=30), nullable=False, server_default="medium"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("dataset_id"),
        )

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("dataset_catalogs")}
    if op.f("ix_dataset_catalogs_name") not in indexes:
        op.create_index(op.f("ix_dataset_catalogs_name"), "dataset_catalogs", ["name"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("dataset_catalogs"):
        indexes = {index["name"] for index in inspector.get_indexes("dataset_catalogs")}
        if op.f("ix_dataset_catalogs_name") in indexes:
            op.drop_index(op.f("ix_dataset_catalogs_name"), table_name="dataset_catalogs")
        op.drop_table("dataset_catalogs")
