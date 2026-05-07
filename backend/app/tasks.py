from __future__ import annotations

from sqlalchemy.orm import joinedload

from app.audit import create_system_audit_log
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import ImageRecord
from app.report_revisions import create_system_report_revision
from app.services import finalize_image_record
from app.storage import storage_service


@celery_app.task(name='image_analysis.run')
def run_image_analysis(image_id: str) -> None:
    db = SessionLocal()
    try:
        image = db.get(ImageRecord, image_id, options=[joinedload(ImageRecord.report)])
        if image is None:
            return

        stored_file = storage_service.load_file(image)
        analysis_result = finalize_image_record(image, image_bytes=stored_file.content)
        if image.report is not None:
            create_system_audit_log(
                db,
                action='report.pdf_generated',
                resource_type='report',
                resource_id=image.report.report_id,
                detail={
                    'image_id': image.image_id,
                    'pdf_variant': image.report.pdf_variant,
                },
            )
            create_system_report_revision(db, report=image.report, status='ai_generated')
        create_system_audit_log(
            db,
            action='analysis.completed',
            resource_type='image',
            resource_id=image.image_id,
            detail={
                'patient_id': image.patient_id,
                'report_status': image.report.status if image.report else None,
                'image_status': image.status,
                'analysis_source': analysis_result['source'],
                'analysis_model': analysis_result['model'],
                'analysis_error': analysis_result['error'],
                'detection_count': len(image.detections),
            },
        )
        db.commit()
    except Exception as exc:
        if 'image' in locals() and image is not None:
            image.status = 'failed'
            if image.report is not None:
                image.report.status = 'processing'
            create_system_audit_log(
                db,
                action='analysis.failed',
                resource_type='image',
                resource_id=image.image_id,
                detail={
                    'error': str(exc),
                },
            )
            db.commit()
        raise
    finally:
        db.close()
