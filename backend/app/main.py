import asyncio
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Response, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.audit import count_audit_logs, create_user_audit_log, list_audit_logs, serialize_audit_log
from app.auth import AuthInfo, authorize_websocket, build_auth_profile, build_rbac_model_payload, ensure_scopes, require_api_auth
from app.config import ALLOWED_ORIGINS
from app.database import SessionLocal, get_db
from app.models import AuditLogRecord, ImageRecord, ReportRecord
from app.schemas import (
    AnalysisListResponse,
    AnalysisResponse,
    AuditLogListResponse,
    DashboardSummaryResponse,
    ImageType,
    ReportReviewRequest,
    ReportReviewResponse,
    ReportStatus,
    UploadApiResponse,
)
from app.services import build_dashboard_summary, build_image_record, serialize_analysis
from app.storage import storage_service
from app.tasks import run_image_analysis

app = FastAPI(title="Wisdom Tooth AI MVP API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_image_or_404(db: Session, image_id: str) -> ImageRecord:
    image = db.get(ImageRecord, image_id, options=[joinedload(ImageRecord.report)])
    if image is None:
        raise HTTPException(status_code=404, detail="未找到对应影像分析结果")
    return image


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "Wisdom Tooth AI MVP API",
        "status": "ok",
        "storage": "postgresql",
        "endpoints": [
            "/api/v1/images/upload",
            "/api/v1/analysis/{image_id}",
            "/api/v1/reports/{report_id}/review",
            "/ws/analysis/{image_id}",
        ],
    }


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ok"}


@app.get("/api/v1/auth/me")
def get_auth_profile(auth: AuthInfo = Depends(require_api_auth(enforce_role_claim=False))) -> dict[str, Any]:
    return {"code": 200, "data": build_auth_profile(auth)}


@app.get("/api/v1/auth/rbac-model")
def get_rbac_model(_: AuthInfo = Depends(require_api_auth(enforce_role_claim=False))) -> dict[str, Any]:
    return {"code": 200, "data": build_rbac_model_payload()}


@app.get("/api/v1/audit-logs", response_model=AuditLogListResponse)
def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    actor_sub: str | None = Query(default=None),
    _: AuthInfo = Depends(require_api_auth('review:reports')),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    items = list_audit_logs(
        db,
        limit=limit,
        offset=offset,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_sub=actor_sub,
    )
    total = count_audit_logs(
        db,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_sub=actor_sub,
    )
    return {"code": 200, "data": [serialize_audit_log(item) for item in items], "meta": {"limit": limit, "offset": offset, "total": total}}


@app.get("/api/v1/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    _: AuthInfo = Depends(require_api_auth('read:images')),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    images = db.execute(
        select(ImageRecord).options(joinedload(ImageRecord.report)).order_by(ImageRecord.created_at.desc())
    ).unique().scalars().all()
    audit_count = db.scalar(select(func.count()).select_from(AuditLogRecord)) or 0
    return {"code": 200, "data": build_dashboard_summary(images, audit_count)}


@app.get("/api/v1/images", response_model=AnalysisListResponse)
def list_images(
    patient_id: str | None = Query(default=None),
    image_type: ImageType | None = Query(default=None),
    report_status: ReportStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: AuthInfo = Depends(require_api_auth('read:images')),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = select(ImageRecord).options(joinedload(ImageRecord.report)).order_by(ImageRecord.created_at.desc())
    count_statement = select(func.count()).select_from(ImageRecord)
    if patient_id:
        statement = statement.where(ImageRecord.patient_id.ilike(f"%{patient_id}%"))
        count_statement = count_statement.where(ImageRecord.patient_id.ilike(f"%{patient_id}%"))
    if image_type:
        statement = statement.where(ImageRecord.image_type == image_type)
        count_statement = count_statement.where(ImageRecord.image_type == image_type)
    if report_status:
        statement = statement.join(ImageRecord.report).where(ReportRecord.status == report_status)
        count_statement = count_statement.join(ImageRecord.report).where(ReportRecord.status == report_status)
    total = db.scalar(count_statement) or 0
    items = db.execute(statement.offset(offset).limit(limit)).unique().scalars().all()
    return {"code": 200, "data": [serialize_analysis(item) for item in items], "meta": {"limit": limit, "offset": offset, "total": total}}


@app.post("/api/v1/images/upload", response_model=UploadApiResponse)
async def upload_image(
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    image_type: ImageType = Form(...),
    auth: AuthInfo = Depends(require_api_auth('upload:images')),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    image = build_image_record(
        patient_id=patient_id,
        image_type=image_type,
        filename=file.filename or 'image.bin',
        stored_path="",
    )
    db.add(image)
    db.flush()

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail='上传文件为空，请重新选择影像文件')
    stored_object = storage_service.save_upload(
        file_bytes=file_bytes,
        filename=file.filename or 'image.bin',
        content_type=file.content_type,
    )
    image.filename = file.filename or 'image.bin'
    image.file_path = stored_object.file_path
    image.storage_provider = stored_object.provider
    image.storage_bucket = stored_object.bucket
    image.storage_object_key = stored_object.object_key

    create_user_audit_log(
        db,
        auth=auth,
        action='image.uploaded',
        resource_type='image',
        resource_id=image.image_id,
        detail={
            'patient_id': patient_id,
            'image_type': image_type,
            'filename': image.filename,
            'storage_provider': image.storage_provider,
        },
    )

    db.commit()
    db.refresh(image)

    try:
        task = run_image_analysis.delay(image.image_id)
    except Exception as exc:  # noqa: BLE001
        image = get_image_or_404(db, image.image_id)
        image.status = 'failed'
        create_user_audit_log(
            db,
            auth=auth,
            action='analysis.enqueue_failed',
            resource_type='image',
            resource_id=image.image_id,
            detail={
                'error': str(exc),
            },
        )
        db.commit()
        raise HTTPException(status_code=503, detail='分析任务队列不可用，请稍后重试') from exc

    create_user_audit_log(
        db,
        auth=auth,
        action='analysis.queued',
        resource_type='image',
        resource_id=image.image_id,
        detail={
            'task_id': task.id,
            'patient_id': image.patient_id,
            'image_type': image.image_type,
        },
    )
    db.commit()

    return {
        "code": 200,
        "data": {
            "image_id": image.image_id,
            "status": image.status,
            "message": "影像已接收，正在分析",
        },
    }


@app.get("/api/v1/analysis/{image_id}", response_model=AnalysisResponse)
def get_analysis(image_id: str, _: AuthInfo = Depends(require_api_auth('read:images')), db: Session = Depends(get_db)) -> dict[str, Any]:
    image = get_image_or_404(db, image_id)
    return {"code": 200, "data": serialize_analysis(image)}


@app.get("/api/v1/images/{image_id}/file")
def get_image_file(image_id: str, _: AuthInfo = Depends(require_api_auth('read:images')), db: Session = Depends(get_db)) -> Response:
    image = get_image_or_404(db, image_id)
    stored = storage_service.load_file(image)
    return Response(content=stored.content, media_type=stored.media_type)


@app.put("/api/v1/reports/{report_id}/review", response_model=ReportReviewResponse)
def review_report(
    report_id: str,
    payload: ReportReviewRequest,
    auth: AuthInfo = Depends(require_api_auth('review:reports')),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = select(ReportRecord).options(joinedload(ReportRecord.image)).where(ReportRecord.report_id == report_id)
    report = db.execute(statement).unique().scalar_one_or_none()
    if report is None or report.image is None:
        raise HTTPException(status_code=404, detail="未找到对应报告")
    if report.status == 'processing' or report.image.status == 'processing':
        raise HTTPException(status_code=409, detail="AI 分析尚未完成，暂不能审核报告")
    if payload.status == 'finalized':
        ensure_scopes(auth, ('finalize:reports',))

    report.doctor_review = payload.doctor_review
    report.status = payload.status
    if payload.modified_findings:
        report.image.detections = payload.modified_findings

    create_user_audit_log(
        db,
        auth=auth,
        action='report.finalized' if payload.status == 'finalized' else 'report.reviewed',
        resource_type='report',
        resource_id=report.report_id,
        detail={
            'image_id': report.image.image_id,
            'report_status': payload.status,
            'findings_modified': bool(payload.modified_findings),
        },
    )

    db.commit()
    db.refresh(report)
    db.refresh(report.image)

    return {
        "code": 200,
        "data": {
            "report_id": report.report_id,
            "status": report.status,
            "doctor_review": report.doctor_review,
            "detections": report.image.detections,
        },
    }


@app.websocket("/ws/analysis/{image_id}")
async def analysis_socket(websocket: WebSocket, image_id: str) -> None:
    await websocket.accept()
    await authorize_websocket(websocket, 'read:images')
    db = SessionLocal()
    try:
        image = db.get(ImageRecord, image_id, options=[joinedload(ImageRecord.report)])
        if image is None or image.report is None:
            await websocket.send_json({"event": "analysis.not_found", "image_id": image_id})
            await websocket.close()
            return
    finally:
        db.close()

    await websocket.send_json({"event": "image.received", "image_id": image_id, "status": "processing"})
    await asyncio.sleep(0.4)
    await websocket.send_json({"event": "ai.detecting", "image_id": image_id, "status": "processing"})

    for _ in range(10):
        await asyncio.sleep(0.4)
        db = SessionLocal()
        try:
            image = db.get(ImageRecord, image_id, options=[joinedload(ImageRecord.report)])
            if image is None or image.report is None:
                await websocket.send_json({"event": "analysis.not_found", "image_id": image_id})
                await websocket.close()
                return
            if image.status != 'processing':
                await websocket.send_json({"event": "ai.completed", "image_id": image_id, "status": image.status})
                await websocket.send_json(
                    {
                        "event": "report.generated",
                        "image_id": image_id,
                        "status": image.report.status,
                        "report_id": image.report.report_id,
                    }
                )
                await websocket.close()
                return
        finally:
            db.close()

    await websocket.send_json({"event": "analysis.pending", "image_id": image_id, "status": "processing"})
    await websocket.close()
