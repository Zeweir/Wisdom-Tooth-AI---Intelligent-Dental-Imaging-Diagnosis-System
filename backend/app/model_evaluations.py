from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ModelEvaluationRecord
from app.schemas import ModelEvaluationCreateRequest


def serialize_model_evaluation(item: ModelEvaluationRecord) -> dict[str, Any]:
    return {
        'evaluation_id': item.evaluation_id,
        'model_name': item.model_name,
        'model_version': item.model_version,
        'dataset_id': item.dataset_id,
        'import_id': item.import_id,
        'precision': item.precision,
        'recall': item.recall,
        'map_score': item.map_score,
        'f1_score': item.f1_score,
        'sample_count': item.sample_count,
        'notes': item.notes,
        'created_at': item.created_at.isoformat(),
    }


def list_model_evaluations(
    db: Session,
    *,
    dataset_id: str | None,
    import_id: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    statement = select(ModelEvaluationRecord).order_by(ModelEvaluationRecord.created_at.desc())
    count_statement = select(func.count()).select_from(ModelEvaluationRecord)
    if dataset_id:
        statement = statement.where(ModelEvaluationRecord.dataset_id == dataset_id)
        count_statement = count_statement.where(ModelEvaluationRecord.dataset_id == dataset_id)
    if import_id:
        statement = statement.where(ModelEvaluationRecord.import_id == import_id)
        count_statement = count_statement.where(ModelEvaluationRecord.import_id == import_id)
    total = db.scalar(count_statement) or 0
    rows = db.execute(statement.offset(offset).limit(limit)).scalars().all()
    return [serialize_model_evaluation(row) for row in rows], total


def create_model_evaluation(db: Session, payload: ModelEvaluationCreateRequest) -> ModelEvaluationRecord:
    item = ModelEvaluationRecord(**payload.model_dump())
    db.add(item)
    return item
