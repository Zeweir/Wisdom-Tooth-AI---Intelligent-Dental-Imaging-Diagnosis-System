"""add audit log records

Revision ID: 20260427_0003
Revises: 20260427_0002
Create Date: 2026-04-27 18:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260427_0003"
down_revision = "20260427_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("audit_log_records"):
        op.create_table(
            "audit_log_records",
            sa.Column("audit_log_id", sa.String(length=36), nullable=False),
            sa.Column("actor_sub", sa.String(length=255), nullable=False),
            sa.Column("actor_client_id", sa.String(length=255), nullable=True),
            sa.Column("actor_organization_id", sa.String(length=255), nullable=True),
            sa.Column("actor_roles", sa.JSON(), nullable=False),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("resource_type", sa.String(length=50), nullable=False),
            sa.Column("resource_id", sa.String(length=36), nullable=False),
            sa.Column("detail", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("audit_log_id"),
        )

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("audit_log_records")}
    if op.f("ix_audit_log_records_actor_sub") not in indexes:
        op.create_index(op.f("ix_audit_log_records_actor_sub"), "audit_log_records", ["actor_sub"], unique=False)
    if op.f("ix_audit_log_records_action") not in indexes:
        op.create_index(op.f("ix_audit_log_records_action"), "audit_log_records", ["action"], unique=False)
    if op.f("ix_audit_log_records_resource_type") not in indexes:
        op.create_index(op.f("ix_audit_log_records_resource_type"), "audit_log_records", ["resource_type"], unique=False)
    if op.f("ix_audit_log_records_resource_id") not in indexes:
        op.create_index(op.f("ix_audit_log_records_resource_id"), "audit_log_records", ["resource_id"], unique=False)
    if op.f("ix_audit_log_records_created_at") not in indexes:
        op.create_index(op.f("ix_audit_log_records_created_at"), "audit_log_records", ["created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("audit_log_records"):
        indexes = {index["name"] for index in inspector.get_indexes("audit_log_records")}
        if op.f("ix_audit_log_records_created_at") in indexes:
            op.drop_index(op.f("ix_audit_log_records_created_at"), table_name="audit_log_records")
        if op.f("ix_audit_log_records_resource_id") in indexes:
            op.drop_index(op.f("ix_audit_log_records_resource_id"), table_name="audit_log_records")
        if op.f("ix_audit_log_records_resource_type") in indexes:
            op.drop_index(op.f("ix_audit_log_records_resource_type"), table_name="audit_log_records")
        if op.f("ix_audit_log_records_action") in indexes:
            op.drop_index(op.f("ix_audit_log_records_action"), table_name="audit_log_records")
        if op.f("ix_audit_log_records_actor_sub") in indexes:
            op.drop_index(op.f("ix_audit_log_records_actor_sub"), table_name="audit_log_records")
        op.drop_table("audit_log_records")
