"""add structured reports and pdf fields

Revision ID: 20260507_0008
Revises: 20260429_0007
Create Date: 2026-05-07 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260507_0008"
down_revision = "20260429_0007"
branch_labels = None
depends_on = None


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {item["name"] for item in inspector.get_columns(table_name)}
    if column.name not in columns:
        op.add_column(table_name, column)


def _drop_column_if_exists(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {item["name"] for item in inspector.get_columns(table_name)}
    if column_name in columns:
        op.drop_column(table_name, column_name)


def upgrade() -> None:
    for table_name in ("report_records", "report_revision_records"):
        _add_column_if_missing(table_name, sa.Column("structured_content", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
        _add_column_if_missing(table_name, sa.Column("pdf_variant", sa.String(length=40), nullable=True))
        _add_column_if_missing(table_name, sa.Column("pdf_file_path", sa.String(length=255), nullable=True))
        _add_column_if_missing(table_name, sa.Column("pdf_storage_provider", sa.String(length=20), nullable=True))
        _add_column_if_missing(table_name, sa.Column("pdf_storage_bucket", sa.String(length=100), nullable=True))
        _add_column_if_missing(table_name, sa.Column("pdf_storage_object_key", sa.String(length=255), nullable=True))
        _add_column_if_missing(table_name, sa.Column("pdf_generated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for table_name in ("report_revision_records", "report_records"):
        for column_name in (
            "pdf_generated_at",
            "pdf_storage_object_key",
            "pdf_storage_bucket",
            "pdf_storage_provider",
            "pdf_file_path",
            "pdf_variant",
            "structured_content",
        ):
            _drop_column_if_exists(table_name, column_name)
