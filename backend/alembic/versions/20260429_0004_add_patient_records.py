"""add patient records

Revision ID: 20260429_0004
Revises: 20260427_0003
Create Date: 2026-04-29 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_0004"
down_revision = "20260427_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("patient_records"):
        op.create_table(
            "patient_records",
            sa.Column("patient_id", sa.String(length=100), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("gender", sa.String(length=20), nullable=True),
            sa.Column("age", sa.Integer(), nullable=True),
            sa.Column("phone", sa.String(length=50), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("patient_id"),
        )

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("patient_records")}
    if op.f("ix_patient_records_name") not in indexes:
        op.create_index(op.f("ix_patient_records_name"), "patient_records", ["name"], unique=False)

    if inspector.has_table("image_records"):
        op.execute(
            """
            INSERT INTO patient_records (patient_id, name, created_at, updated_at)
            SELECT DISTINCT image_records.patient_id, image_records.patient_id, NOW(), NOW()
            FROM image_records
            LEFT JOIN patient_records ON patient_records.patient_id = image_records.patient_id
            WHERE image_records.patient_id IS NOT NULL
              AND patient_records.patient_id IS NULL
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("patient_records"):
        indexes = {index["name"] for index in inspector.get_indexes("patient_records")}
        if op.f("ix_patient_records_name") in indexes:
            op.drop_index(op.f("ix_patient_records_name"), table_name="patient_records")
        op.drop_table("patient_records")
