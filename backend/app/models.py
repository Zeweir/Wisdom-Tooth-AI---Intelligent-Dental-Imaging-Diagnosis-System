from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
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
