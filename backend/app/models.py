from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ImageRecord(Base):
    __tablename__ = 'image_records'

    image_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    patient_id: Mapped[str] = mapped_column(String(100), index=True)
    image_type: Mapped[str] = mapped_column(String(20))
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default='completed')
    storage_provider: Mapped[str] = mapped_column(String(20), default='local')
    storage_bucket: Mapped[str | None] = mapped_column(String(100), nullable=True)
    storage_object_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detections: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    segmentation_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    report: Mapped['ReportRecord'] = relationship(
        back_populates='image',
        cascade='all, delete-orphan',
        uselist=False,
    )


class PatientRecord(Base):
    __tablename__ = 'patient_records'

    patient_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class DatasetCatalogRecord(Base):
    __tablename__ = 'dataset_catalogs'

    dataset_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(160), index=True)
    source_name: Mapped[str] = mapped_column(String(120))
    homepage_url: Mapped[str] = mapped_column(String(500))
    paper_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license: Mapped[str | None] = mapped_column(String(120), nullable=True)
    image_type: Mapped[str] = mapped_column(String(40), default='panoramic')
    task_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    disease_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    sample_size: Mapped[str | None] = mapped_column(String(120), nullable=True)
    annotation_format: Mapped[str | None] = mapped_column(String(160), nullable=True)
    access_status: Mapped[str] = mapped_column(String(40), default='open')
    priority: Mapped[str] = mapped_column(String(30), default='medium')
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class DatasetImportRecord(Base):
    __tablename__ = 'dataset_import_records'

    import_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey('dataset_catalogs.dataset_id'), index=True)
    import_method: Mapped[str] = mapped_column(String(40))
    source_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    storage_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    storage_bucket: Mapped[str | None] = mapped_column(String(100), nullable=True)
    storage_object_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    annotation_format: Mapped[str | None] = mapped_column(String(160), nullable=True)
    image_type: Mapped[str] = mapped_column(String(40), default='panoramic')
    status: Mapped[str] = mapped_column(String(40), default='created')
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    dataset: Mapped[DatasetCatalogRecord] = relationship()


class DatasetSampleRecord(Base):
    __tablename__ = 'dataset_sample_records'

    sample_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    import_id: Mapped[str] = mapped_column(String(36), ForeignKey('dataset_import_records.import_id'), index=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey('dataset_catalogs.dataset_id'), index=True)
    filename: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(40), default='unknown')
    image_type: Mapped[str] = mapped_column(String(40), default='panoramic')
    annotation_status: Mapped[str] = mapped_column(String(40), default='unknown')
    split: Mapped[str | None] = mapped_column(String(20), nullable=True)
    label_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    storage_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ModelEvaluationRecord(Base):
    __tablename__ = 'model_evaluation_records'

    evaluation_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    model_name: Mapped[str] = mapped_column(String(160))
    model_version: Mapped[str] = mapped_column(String(120))
    dataset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('dataset_catalogs.dataset_id'), nullable=True, index=True)
    import_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('dataset_import_records.import_id'), nullable=True, index=True)
    precision: Mapped[float | None] = mapped_column(nullable=True)
    recall: Mapped[float | None] = mapped_column(nullable=True)
    map_score: Mapped[float | None] = mapped_column(nullable=True)
    f1_score: Mapped[float | None] = mapped_column(nullable=True)
    sample_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class ReportRecord(Base):
    __tablename__ = 'report_records'

    report_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    image_id: Mapped[str] = mapped_column(String(36), ForeignKey('image_records.image_id'), unique=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    doctor_review: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='ai_generated')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    image: Mapped[ImageRecord] = relationship(back_populates='report')


class ReportRevisionRecord(Base):
    __tablename__ = 'report_revision_records'

    revision_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey('report_records.report_id'), index=True)
    image_id: Mapped[str] = mapped_column(String(36), ForeignKey('image_records.image_id'), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column(Text)
    doctor_review: Mapped[str | None] = mapped_column(Text, nullable=True)
    detections: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    actor_sub: Mapped[str] = mapped_column(String(255), index=True)
    actor_roles: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class AuditLogRecord(Base):
    __tablename__ = 'audit_log_records'

    audit_log_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    actor_sub: Mapped[str] = mapped_column(String(255), index=True)
    actor_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_organization_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_roles: Mapped[list[str]] = mapped_column(JSON)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(50), index=True)
    resource_id: Mapped[str] = mapped_column(String(36), index=True)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
