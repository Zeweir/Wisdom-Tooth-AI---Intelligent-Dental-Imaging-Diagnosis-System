"""add dataset imports and evaluations

Revision ID: 20260429_0006
Revises: 20260429_0005
Create Date: 2026-04-29 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_0006"
down_revision = "20260429_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("dataset_import_records"):
        op.create_table(
            "dataset_import_records",
            sa.Column("import_id", sa.String(length=36), nullable=False),
            sa.Column("dataset_id", sa.String(length=36), nullable=False),
            sa.Column("import_method", sa.String(length=40), nullable=False),
            sa.Column("source_path", sa.String(length=500), nullable=True),
            sa.Column("storage_provider", sa.String(length=20), nullable=True),
            sa.Column("storage_bucket", sa.String(length=100), nullable=True),
            sa.Column("storage_object_key", sa.String(length=255), nullable=True),
            sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("annotation_format", sa.String(length=160), nullable=True),
            sa.Column("image_type", sa.String(length=40), nullable=False, server_default="panoramic"),
            sa.Column("status", sa.String(length=40), nullable=False, server_default="created"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["dataset_id"], ["dataset_catalogs.dataset_id"]),
            sa.PrimaryKeyConstraint("import_id"),
        )
        op.create_index(op.f("ix_dataset_import_records_dataset_id"), "dataset_import_records", ["dataset_id"], unique=False)

    if not inspector.has_table("dataset_sample_records"):
        op.create_table(
            "dataset_sample_records",
            sa.Column("sample_id", sa.String(length=36), nullable=False),
            sa.Column("import_id", sa.String(length=36), nullable=False),
            sa.Column("dataset_id", sa.String(length=36), nullable=False),
            sa.Column("filename", sa.String(length=500), nullable=False),
            sa.Column("file_type", sa.String(length=40), nullable=False, server_default="unknown"),
            sa.Column("image_type", sa.String(length=40), nullable=False, server_default="panoramic"),
            sa.Column("annotation_status", sa.String(length=40), nullable=False, server_default="unknown"),
            sa.Column("split", sa.String(length=20), nullable=True),
            sa.Column("label_summary", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("storage_object_key", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["dataset_id"], ["dataset_catalogs.dataset_id"]),
            sa.ForeignKeyConstraint(["import_id"], ["dataset_import_records.import_id"]),
            sa.PrimaryKeyConstraint("sample_id"),
        )
        op.create_index(op.f("ix_dataset_sample_records_dataset_id"), "dataset_sample_records", ["dataset_id"], unique=False)
        op.create_index(op.f("ix_dataset_sample_records_import_id"), "dataset_sample_records", ["import_id"], unique=False)

    if not inspector.has_table("model_evaluation_records"):
        op.create_table(
            "model_evaluation_records",
            sa.Column("evaluation_id", sa.String(length=36), nullable=False),
            sa.Column("model_name", sa.String(length=160), nullable=False),
            sa.Column("model_version", sa.String(length=120), nullable=False),
            sa.Column("dataset_id", sa.String(length=36), nullable=True),
            sa.Column("import_id", sa.String(length=36), nullable=True),
            sa.Column("precision", sa.Float(), nullable=True),
            sa.Column("recall", sa.Float(), nullable=True),
            sa.Column("map_score", sa.Float(), nullable=True),
            sa.Column("f1_score", sa.Float(), nullable=True),
            sa.Column("sample_count", sa.Integer(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["dataset_id"], ["dataset_catalogs.dataset_id"]),
            sa.ForeignKeyConstraint(["import_id"], ["dataset_import_records.import_id"]),
            sa.PrimaryKeyConstraint("evaluation_id"),
        )
        op.create_index(op.f("ix_model_evaluation_records_created_at"), "model_evaluation_records", ["created_at"], unique=False)
        op.create_index(op.f("ix_model_evaluation_records_dataset_id"), "model_evaluation_records", ["dataset_id"], unique=False)
        op.create_index(op.f("ix_model_evaluation_records_import_id"), "model_evaluation_records", ["import_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("model_evaluation_records"):
        indexes = {index["name"] for index in inspector.get_indexes("model_evaluation_records")}
        for name in [
            op.f("ix_model_evaluation_records_import_id"),
            op.f("ix_model_evaluation_records_dataset_id"),
            op.f("ix_model_evaluation_records_created_at"),
        ]:
            if name in indexes:
                op.drop_index(name, table_name="model_evaluation_records")
        op.drop_table("model_evaluation_records")

    if inspector.has_table("dataset_sample_records"):
        indexes = {index["name"] for index in inspector.get_indexes("dataset_sample_records")}
        for name in [op.f("ix_dataset_sample_records_import_id"), op.f("ix_dataset_sample_records_dataset_id")]:
            if name in indexes:
                op.drop_index(name, table_name="dataset_sample_records")
        op.drop_table("dataset_sample_records")

    if inspector.has_table("dataset_import_records"):
        indexes = {index["name"] for index in inspector.get_indexes("dataset_import_records")}
        if op.f("ix_dataset_import_records_dataset_id") in indexes:
            op.drop_index(op.f("ix_dataset_import_records_dataset_id"), table_name="dataset_import_records")
        op.drop_table("dataset_import_records")
