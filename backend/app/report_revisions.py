from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import AuthInfo
from app.clinical_reports import normalize_structured_report_payload
from app.models import ReportRecord, ReportRevisionRecord


def serialize_report_revision(revision: ReportRevisionRecord) -> dict[str, Any]:
    return {
        'revision_id': revision.revision_id,
        'report_id': revision.report_id,
        'image_id': revision.image_id,
        'version_no': revision.version_no,
        'status': revision.status,
        'content': revision.content,
        'structured_content': normalize_structured_report_payload(revision.structured_content),
        'doctor_review': revision.doctor_review,
        'detections': revision.detections,
        'pdf_url': f"/api/v1/reports/{revision.report_id}/revisions/{revision.revision_id}/pdf" if revision.pdf_file_path or revision.pdf_storage_object_key else None,
        'pdf_variant': revision.pdf_variant,
        'pdf_generated_at': revision.pdf_generated_at.isoformat() if revision.pdf_generated_at else None,
        'actor_sub': revision.actor_sub,
        'actor_roles': revision.actor_roles,
        'created_at': revision.created_at.isoformat(),
    }


def count_report_revisions(db: Session, report_id: str) -> int:
    return db.scalar(
        select(func.count()).select_from(ReportRevisionRecord).where(ReportRevisionRecord.report_id == report_id)
    ) or 0


def list_report_revisions(db: Session, *, report_id: str, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    total = count_report_revisions(db, report_id)
    rows = db.execute(
        select(ReportRevisionRecord)
        .where(ReportRevisionRecord.report_id == report_id)
        .order_by(ReportRevisionRecord.version_no.desc(), ReportRevisionRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()
    return [serialize_report_revision(row) for row in rows], total


def create_report_revision(
    db: Session,
    *,
    report: ReportRecord,
    auth: AuthInfo,
    status: str | None = None,
) -> ReportRevisionRecord:
    if report.image is None:
        raise ValueError('report image relation must be loaded before creating report revision')
    version_no = count_report_revisions(db, report.report_id) + 1
    revision = ReportRevisionRecord(
        report_id=report.report_id,
        image_id=report.image.image_id,
        version_no=version_no,
        status=status or report.status,
        content=report.content,
        structured_content=report.structured_content or {},
        doctor_review=report.doctor_review,
        detections=report.image.detections or [],
        pdf_variant=report.pdf_variant,
        pdf_file_path=report.pdf_file_path,
        pdf_storage_provider=report.pdf_storage_provider,
        pdf_storage_bucket=report.pdf_storage_bucket,
        pdf_storage_object_key=report.pdf_storage_object_key,
        pdf_generated_at=report.pdf_generated_at,
        actor_sub=auth.sub,
        actor_roles=auth.effective_roles,
    )
    db.add(revision)
    return revision


def ensure_initial_report_revision(db: Session, *, report: ReportRecord, auth: AuthInfo) -> ReportRevisionRecord | None:
    if count_report_revisions(db, report.report_id) > 0:
        return None
    return create_report_revision(db, report=report, auth=auth, status='ai_generated')


def create_system_report_revision(db: Session, *, report: ReportRecord, status: str | None = None) -> ReportRevisionRecord:
    if report.image is None:
        raise ValueError('report image relation must be loaded before creating report revision')
    version_no = count_report_revisions(db, report.report_id) + 1
    revision = ReportRevisionRecord(
        report_id=report.report_id,
        image_id=report.image.image_id,
        version_no=version_no,
        status=status or report.status,
        content=report.content,
        structured_content=report.structured_content or {},
        doctor_review=report.doctor_review,
        detections=report.image.detections or [],
        pdf_variant=report.pdf_variant,
        pdf_file_path=report.pdf_file_path,
        pdf_storage_provider=report.pdf_storage_provider,
        pdf_storage_bucket=report.pdf_storage_bucket,
        pdf_storage_object_key=report.pdf_storage_object_key,
        pdf_generated_at=report.pdf_generated_at,
        actor_sub='system',
        actor_roles=['system'],
    )
    db.add(revision)
    return revision
