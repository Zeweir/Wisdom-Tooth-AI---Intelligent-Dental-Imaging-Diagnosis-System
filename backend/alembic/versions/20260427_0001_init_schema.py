"""init schema

Revision ID: 20260427_0001
Revises: 
Create Date: 2026-04-27 15:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260427_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("image_records"):
        op.create_table(
            "image_records",
            sa.Column("image_id", sa.String(length=36), nullable=False),
            sa.Column("patient_id", sa.String(length=100), nullable=False),
            sa.Column("image_type", sa.String(length=20), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("file_path", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("detections", sa.JSON(), nullable=False),
            sa.Column("segmentation_url", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("image_id"),
        )

    image_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("image_records")}
    if op.f("ix_image_records_patient_id") not in image_indexes:
        op.create_index(op.f("ix_image_records_patient_id"), "image_records", ["patient_id"], unique=False)

    if not inspector.has_table("report_records"):
        op.create_table(
            "report_records",
            sa.Column("report_id", sa.String(length=36), nullable=False),
            sa.Column("image_id", sa.String(length=36), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("doctor_review", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["image_id"], ["image_records.image_id"]),
            sa.PrimaryKeyConstraint("report_id"),
        )

    report_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("report_records")}
    if op.f("ix_report_records_image_id") not in report_indexes:
        op.create_index(op.f("ix_report_records_image_id"), "report_records", ["image_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_report_records_image_id"), table_name="report_records")
    op.drop_table("report_records")
    op.drop_index(op.f("ix_image_records_patient_id"), table_name="image_records")
    op.drop_table("image_records")
