from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import ImageRecord, PatientRecord
from app.schemas import PatientCreateRequest, PatientUpdateRequest
from app.services import now_utc


def serialize_patient(patient: PatientRecord, *, image_count: int = 0, latest_image_at: Any = None) -> dict[str, Any]:
    return {
        'patient_id': patient.patient_id,
        'name': patient.name,
        'gender': patient.gender,
        'age': patient.age,
        'phone': patient.phone,
        'notes': patient.notes,
        'image_count': image_count,
        'latest_image_at': latest_image_at.isoformat() if hasattr(latest_image_at, 'isoformat') else latest_image_at,
        'created_at': patient.created_at.isoformat(),
        'updated_at': patient.updated_at.isoformat(),
    }


def serialize_patient_summary(patient: PatientRecord | None) -> dict[str, Any] | None:
    if patient is None:
        return None
    return {
        'patient_id': patient.patient_id,
        'name': patient.name,
        'gender': patient.gender,
        'age': patient.age,
        'phone': patient.phone,
    }


def get_patient_stats(db: Session, patient_id: str) -> tuple[int, Any]:
    statement = select(func.count(ImageRecord.image_id), func.max(ImageRecord.created_at)).where(ImageRecord.patient_id == patient_id)
    image_count, latest_image_at = db.execute(statement).one()
    return int(image_count or 0), latest_image_at


def get_patient_or_404(db: Session, patient_id: str) -> PatientRecord:
    patient = db.get(PatientRecord, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail='未找到对应患者档案')
    return patient


def ensure_patient_record(db: Session, *, patient_id: str, name: str | None = None) -> PatientRecord:
    patient = db.get(PatientRecord, patient_id)
    if patient is not None:
        return patient
    patient = PatientRecord(
        patient_id=patient_id,
        name=name or patient_id,
        gender=None,
        age=None,
        phone=None,
        notes='由影像上传流程自动创建的最小患者档案。',
    )
    db.add(patient)
    return patient


def create_patient(db: Session, payload: PatientCreateRequest) -> PatientRecord:
    if db.get(PatientRecord, payload.patient_id) is not None:
        raise HTTPException(status_code=409, detail='患者编号已存在')
    patient = PatientRecord(
        patient_id=payload.patient_id,
        name=payload.name,
        gender=payload.gender,
        age=payload.age,
        phone=payload.phone,
        notes=payload.notes,
    )
    db.add(patient)
    return patient


def update_patient(db: Session, patient_id: str, payload: PatientUpdateRequest) -> PatientRecord:
    patient = get_patient_or_404(db, patient_id)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)
    patient.updated_at = now_utc()
    return patient


def list_patients(db: Session, *, keyword: str | None, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    stats_subquery = (
        select(
            ImageRecord.patient_id.label('patient_id'),
            func.count(ImageRecord.image_id).label('image_count'),
            func.max(ImageRecord.created_at).label('latest_image_at'),
        )
        .group_by(ImageRecord.patient_id)
        .subquery()
    )
    statement = (
        select(PatientRecord, stats_subquery.c.image_count, stats_subquery.c.latest_image_at)
        .outerjoin(stats_subquery, stats_subquery.c.patient_id == PatientRecord.patient_id)
        .order_by(PatientRecord.updated_at.desc())
    )
    count_statement = select(func.count()).select_from(PatientRecord)
    if keyword:
        condition = or_(PatientRecord.patient_id.ilike(f'%{keyword}%'), PatientRecord.name.ilike(f'%{keyword}%'))
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

    total = db.scalar(count_statement) or 0
    rows = db.execute(statement.offset(offset).limit(limit)).all()
    return [
        serialize_patient(patient, image_count=int(image_count or 0), latest_image_at=latest_image_at)
        for patient, image_count, latest_image_at in rows
    ], total
