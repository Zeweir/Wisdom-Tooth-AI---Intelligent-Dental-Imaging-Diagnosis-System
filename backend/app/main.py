import asyncio
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Response, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.auth import AuthInfo, authorize_websocket, build_auth_profile, build_rbac_model_payload, ensure_scopes, require_api_auth
from app.config import ALLOWED_ORIGINS
from app.database import SessionLocal, get_db
from app.models import ImageRecord, ReportRecord
from app.schemas import ImageType, ReportReviewRequest, ReportStatus
from app.services import build_image_record, finalize_image_record, serialize_analysis
from app.storage import storage_service

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


async def process_image_analysis(image_id: str) -> None:
    await asyncio.sleep(1.2)
    db = SessionLocal()
    try:
        image = db.get(ImageRecord, image_id, options=[joinedload(ImageRecord.report)])
        if image is None:
            return
        finalize_image_record(image)
        db.commit()
    finally:
        db.close()


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
def get_auth_profile(auth: AuthInfo = Depends(require_api_auth())) -> dict[str, Any]:
    return {"code": 200, "data": build_auth_profile(auth)}


@app.get("/api/v1/auth/rbac-model")
def get_rbac_model(_: AuthInfo = Depends(require_api_auth())) -> dict[str, Any]:
    return {"code": 200, "data": build_rbac_model_payload()}


@app.get("/api/v1/images")
def list_images(
    patient_id: str | None = Query(default=None),
    image_type: ImageType | None = Query(default=None),
    report_status: ReportStatus | None = Query(default=None),
    _: AuthInfo = Depends(require_api_auth('read:images')),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = select(ImageRecord).options(joinedload(ImageRecord.report)).order_by(ImageRecord.created_at.desc())
    if patient_id:
        statement = statement.where(ImageRecord.patient_id.ilike(f"%{patient_id}%"))
    if image_type:
        statement = statement.where(ImageRecord.image_type == image_type)
    if report_status:
        statement = statement.join(ImageRecord.report).where(ReportRecord.status == report_status)
    items = db.execute(statement).unique().scalars().all()
    return {"code": 200, "data": [serialize_analysis(item) for item in items]}


@app.post("/api/v1/images/upload")
async def upload_image(
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    image_type: ImageType = Form(...),
    _: AuthInfo = Depends(require_api_auth('upload:images')),
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

    db.commit()
    db.refresh(image)
    asyncio.create_task(process_image_analysis(image.image_id))

    return {
        "code": 200,
        "data": {
            "image_id": image.image_id,
            "status": image.status,
            "message": "影像已接收，正在分析",
        },
    }


@app.get("/api/v1/analysis/{image_id}")
def get_analysis(image_id: str, _: AuthInfo = Depends(require_api_auth('read:images')), db: Session = Depends(get_db)) -> dict[str, Any]:
    image = get_image_or_404(db, image_id)
    return {"code": 200, "data": serialize_analysis(image)}


@app.get("/api/v1/images/{image_id}/file")
def get_image_file(image_id: str, _: AuthInfo = Depends(require_api_auth('read:images')), db: Session = Depends(get_db)) -> Response:
    image = get_image_or_404(db, image_id)
    stored = storage_service.load_file(image)
    return Response(content=stored.content, media_type=stored.media_type)


@app.put("/api/v1/reports/{report_id}/review")
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
