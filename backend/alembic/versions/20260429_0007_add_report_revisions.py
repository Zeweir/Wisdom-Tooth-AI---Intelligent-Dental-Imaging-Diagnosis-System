"""add report revisions

Revision ID: 20260429_0007
Revises: 20260429_0006
Create Date: 2026-04-29 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_0007"
down_revision = "20260429_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("report_revision_records"):
        op.create_table(
            "report_revision_records",
            sa.Column("revision_id", sa.String(length=36), nullable=False),
            sa.Column("report_id", sa.String(length=36), nullable=False),
            sa.Column("image_id", sa.String(length=36), nullable=False),
            sa.Column("version_no", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("doctor_review", sa.Text(), nullable=True),
            sa.Column("detections", sa.JSON(), nullable=False),
            sa.Column("actor_sub", sa.String(length=255), nullable=False),
            sa.Column("actor_roles", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["image_id"], ["image_records.image_id"]),
            sa.ForeignKeyConstraint(["report_id"], ["report_records.report_id"]),
            sa.PrimaryKeyConstraint("revision_id"),
        )
        op.create_index(op.f("ix_report_revision_records_actor_sub"), "report_revision_records", ["actor_sub"], unique=False)
        op.create_index(op.f("ix_report_revision_records_created_at"), "report_revision_records", ["created_at"], unique=False)
        op.create_index(op.f("ix_report_revision_records_image_id"), "report_revision_records", ["image_id"], unique=False)
        op.create_index(op.f("ix_report_revision_records_report_id"), "report_revision_records", ["report_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("report_revision_records"):
        indexes = {index["name"] for index in inspector.get_indexes("report_revision_records")}
        for name in [
            op.f("ix_report_revision_records_report_id"),
            op.f("ix_report_revision_records_image_id"),
            op.f("ix_report_revision_records_created_at"),
            op.f("ix_report_revision_records_actor_sub"),
        ]:
            if name in indexes:
                op.drop_index(name, table_name="report_revision_records")
        op.drop_table("report_revision_records")
