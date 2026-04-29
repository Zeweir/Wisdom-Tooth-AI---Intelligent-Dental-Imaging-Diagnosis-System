from __future__ import annotations

import random
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.datasets import get_dataset_or_404
from app.models import DatasetImportRecord, DatasetSampleRecord
from app.schemas import DatasetImportCreateRequest, DatasetSplitRequest
from app.services import now_utc
from app.storage import StoredObject


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.dcm'}
ANNOTATION_EXTENSIONS = {'.json', '.txt', '.xml', '.csv'}
MAX_ZIP_SIZE_BYTES = 200 * 1024 * 1024
MAX_INDEXED_FILES = 2000


def infer_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return 'image'
    if suffix in ANNOTATION_EXTENSIONS:
        return 'annotation'
    return 'other'


def serialize_dataset_import(item: DatasetImportRecord) -> dict[str, Any]:
    return {
        'import_id': item.import_id,
        'dataset_id': item.dataset_id,
        'import_method': item.import_method,
        'source_path': item.source_path,
        'storage_provider': item.storage_provider,
        'storage_bucket': item.storage_bucket,
        'storage_object_key': item.storage_object_key,
        'sample_count': item.sample_count,
        'annotation_format': item.annotation_format,
        'image_type': item.image_type,
        'status': item.status,
        'error_message': item.error_message,
        'notes': item.notes,
        'created_at': item.created_at.isoformat(),
        'updated_at': item.updated_at.isoformat(),
    }


def serialize_dataset_sample(item: DatasetSampleRecord) -> dict[str, Any]:
    return {
        'sample_id': item.sample_id,
        'import_id': item.import_id,
        'dataset_id': item.dataset_id,
        'filename': item.filename,
        'file_type': item.file_type,
        'image_type': item.image_type,
        'annotation_status': item.annotation_status,
        'split': item.split,
        'label_summary': item.label_summary or {},
        'storage_object_key': item.storage_object_key,
        'created_at': item.created_at.isoformat(),
    }


def get_import_or_404(db: Session, import_id: str) -> DatasetImportRecord:
    item = db.get(DatasetImportRecord, import_id)
    if item is None:
        raise HTTPException(status_code=404, detail='未找到对应数据导入批次')
    return item


def list_dataset_imports(db: Session, *, dataset_id: str, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    get_dataset_or_404(db, dataset_id)
    statement = (
        select(DatasetImportRecord)
        .where(DatasetImportRecord.dataset_id == dataset_id)
        .order_by(DatasetImportRecord.created_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(DatasetImportRecord).where(DatasetImportRecord.dataset_id == dataset_id)) or 0
    rows = db.execute(statement.offset(offset).limit(limit)).scalars().all()
    return [serialize_dataset_import(row) for row in rows], total


def create_dataset_import(db: Session, *, dataset_id: str, payload: DatasetImportCreateRequest) -> DatasetImportRecord:
    get_dataset_or_404(db, dataset_id)
    status = 'summarized' if payload.import_method == 'manual_summary' else 'registered'
    item = DatasetImportRecord(
        dataset_id=dataset_id,
        import_method=payload.import_method,
        source_path=payload.source_path,
        sample_count=payload.sample_count,
        annotation_format=payload.annotation_format,
        image_type=payload.image_type,
        status=status,
        notes=payload.notes,
    )
    db.add(item)
    db.flush()
    if payload.import_method == 'manual_summary' and payload.sample_count > 0:
        create_placeholder_samples(db, item, payload.sample_count)
    return item


def create_placeholder_samples(db: Session, item: DatasetImportRecord, sample_count: int) -> None:
    capped_count = min(sample_count, 500)
    for index in range(capped_count):
        db.add(
            DatasetSampleRecord(
                import_id=item.import_id,
                dataset_id=item.dataset_id,
                filename=f'manual-sample-{index + 1:04d}',
                file_type='summary',
                image_type=item.image_type,
                annotation_status='summary_only',
                label_summary={'source': 'manual_summary'},
            )
        )


def index_zip_upload(
    db: Session,
    *,
    item: DatasetImportRecord,
    file_bytes: bytes,
    stored_object: StoredObject,
) -> int:
    if len(file_bytes) > MAX_ZIP_SIZE_BYTES:
        raise HTTPException(status_code=413, detail='样本包超过 200MB 限制')
    try:
        archive = zipfile.ZipFile(BytesIO(file_bytes))
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail='上传文件不是有效 zip 样本包') from exc

    names = [name for name in archive.namelist() if not name.endswith('/') and not Path(name).name.startswith('.')]
    indexed = 0
    for name in names[:MAX_INDEXED_FILES]:
        file_type = infer_file_type(name)
        if file_type == 'other':
            continue
        db.add(
            DatasetSampleRecord(
                import_id=item.import_id,
                dataset_id=item.dataset_id,
                filename=name,
                file_type=file_type,
                image_type=item.image_type,
                annotation_status='available' if file_type == 'annotation' else 'unknown',
                label_summary={'archive': stored_object.object_key},
                storage_object_key=stored_object.object_key,
            )
        )
        indexed += 1

    item.storage_provider = stored_object.provider
    item.storage_bucket = stored_object.bucket
    item.storage_object_key = stored_object.object_key
    item.source_path = stored_object.file_path
    item.sample_count = indexed
    item.status = 'indexed'
    item.error_message = None
    item.updated_at = now_utc()
    return indexed


def list_import_samples(db: Session, *, import_id: str, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    get_import_or_404(db, import_id)
    statement = (
        select(DatasetSampleRecord)
        .where(DatasetSampleRecord.import_id == import_id)
        .order_by(DatasetSampleRecord.created_at.asc())
    )
    total = db.scalar(select(func.count()).select_from(DatasetSampleRecord).where(DatasetSampleRecord.import_id == import_id)) or 0
    rows = db.execute(statement.offset(offset).limit(limit)).scalars().all()
    return [serialize_dataset_sample(row) for row in rows], total


def split_import_samples(db: Session, *, import_id: str, payload: DatasetSplitRequest) -> dict[str, int]:
    total_ratio = payload.train_ratio + payload.val_ratio + payload.test_ratio
    if abs(total_ratio - 1.0) > 0.001:
        raise HTTPException(status_code=400, detail='训练/验证/测试比例总和必须为 1')

    item = get_import_or_404(db, import_id)
    samples = db.execute(select(DatasetSampleRecord).where(DatasetSampleRecord.import_id == import_id)).scalars().all()
    if not samples:
        raise HTTPException(status_code=400, detail='当前导入批次没有可划分样本')

    random.Random(42).shuffle(samples)
    total = len(samples)
    train_end = int(total * payload.train_ratio)
    val_end = train_end + int(total * payload.val_ratio)
    counts = {'train': 0, 'val': 0, 'test': 0}
    for index, sample in enumerate(samples):
        if index < train_end:
            sample.split = 'train'
        elif index < val_end:
            sample.split = 'val'
        else:
            sample.split = 'test'
        counts[sample.split] += 1

    item.status = 'split_ready'
    item.updated_at = now_utc()
    return counts
