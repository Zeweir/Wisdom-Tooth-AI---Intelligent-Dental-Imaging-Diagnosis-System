from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models import DatasetCatalogRecord
from app.schemas import DatasetCatalogCreateRequest, DatasetCatalogUpdateRequest
from app.services import now_utc


PUBLIC_DATASET_SEEDS: tuple[dict[str, Any], ...] = (
    {
        'name': 'DENTEX 2023 Challenge',
        'source_name': 'Grand Challenge / Zenodo / Kaggle',
        'homepage_url': 'https://dentex.grand-challenge.org/data/',
        'paper_url': 'https://zenodo.org/records/7812323',
        'license': 'Challenge terms / public research access',
        'image_type': 'panoramic',
        'task_types': ['tooth enumeration', 'diagnosis classification', 'disease detection'],
        'disease_tags': ['caries', 'deep caries', 'periapical lesions', 'impacted teeth'],
        'sample_size': 'Panoramic radiographs for DENTEX 2023 tasks',
        'annotation_format': 'COCO-like / challenge annotations',
        'access_status': 'open_registration',
        'priority': 'high',
        'notes': '优先推荐；直接覆盖智齿阻生、龋齿、根尖病灶等当前系统类别。',
    },
    {
        'name': 'OdontoAI Open Panoramic Radiographs (O2PR)',
        'source_name': 'IvisionLab GitHub',
        'homepage_url': 'https://github.com/IvisionLab/OdontoAI-Open-Panoramic-Radiographs',
        'paper_url': 'https://github.com/IvisionLab/MEDIA-datasets',
        'license': 'Repository license / dataset terms',
        'image_type': 'panoramic',
        'task_types': ['tooth instance segmentation', 'tooth numbering'],
        'disease_tags': ['tooth structure', 'tooth enumeration'],
        'sample_size': '4000 panoramic radiographs, 2000 released annotations',
        'annotation_format': 'instance masks / numbering annotations',
        'access_status': 'open',
        'priority': 'high',
        'notes': '适合先做牙齿定位、编号和实例分割预训练。',
    },
    {
        'name': 'Tufts Dental Database',
        'source_name': 'Tufts / OJP / NIDCR Data Hub',
        'homepage_url': 'https://www.ojp.gov/library/publications/tufts-dental-database-multimodal-panoramic-x-ray-dataset-benchmarking',
        'paper_url': 'https://www.ddshub.nih.gov/data-sources/head-neck-imaging-data',
        'license': 'Data hub terms',
        'image_type': 'panoramic',
        'task_types': ['abnormality detection', 'tooth annotation', 'benchmarking'],
        'disease_tags': ['dental abnormalities', 'tooth structure'],
        'sample_size': '1000 panoramic radiographs',
        'annotation_format': 'expert annotations',
        'access_status': 'application_required',
        'priority': 'medium',
        'notes': '适合做异常检测基准；可能需要按数据平台要求申请访问。',
    },
    {
        'name': 'Panoramic Dental Xray Dataset',
        'source_name': 'Mendeley Data',
        'homepage_url': 'https://data.mendeley.com/datasets/73n3kz2k4k',
        'paper_url': None,
        'license': 'CC BY 4.0',
        'image_type': 'panoramic',
        'task_types': ['tooth segmentation', 'tooth numbering'],
        'disease_tags': ['tooth structure', 'tooth enumeration'],
        'sample_size': 'Panoramic dental x-ray dataset',
        'annotation_format': 'segmentation / numbering annotations',
        'access_status': 'open',
        'priority': 'medium',
        'notes': '许可清晰，适合课程演示和牙齿结构分割 baseline。',
    },
    {
        'name': 'Panoramic Mandible Segmentation',
        'source_name': 'Mendeley Data',
        'homepage_url': 'https://data.mendeley.com/datasets/hxt48yk462/2',
        'paper_url': None,
        'license': 'CC BY-NC 3.0',
        'image_type': 'panoramic',
        'task_types': ['mandible segmentation'],
        'disease_tags': ['mandible', 'jaw bone'],
        'sample_size': '116 anonymous panoramic radiographs',
        'annotation_format': 'segmentation masks',
        'access_status': 'open',
        'priority': 'low',
        'notes': '适合下颌骨分割和解剖结构演示；非商业许可需注意。',
    },
    {
        'name': 'Pediatric Panoramic Caries Dataset',
        'source_name': 'Scientific Data / Mendeley index',
        'homepage_url': 'https://www.mendeley.com/catalogue/4b6db210-87eb-3ceb-8363-b10509556d42/',
        'paper_url': None,
        'license': 'Publication / dataset terms',
        'image_type': 'panoramic',
        'task_types': ['caries segmentation', 'disease detection'],
        'disease_tags': ['caries', 'pediatric dental disease'],
        'sample_size': 'Children panoramic radiographs',
        'annotation_format': 'disease masks / labels',
        'access_status': 'open_reference',
        'priority': 'medium',
        'notes': '适合补充龋齿分割数据，但儿童场景和成人智齿场景需要分开评估。',
    },
)


def serialize_dataset(dataset: DatasetCatalogRecord) -> dict[str, Any]:
    return {
        'dataset_id': dataset.dataset_id,
        'name': dataset.name,
        'source_name': dataset.source_name,
        'homepage_url': dataset.homepage_url,
        'paper_url': dataset.paper_url,
        'license': dataset.license,
        'image_type': dataset.image_type,
        'task_types': dataset.task_types or [],
        'disease_tags': dataset.disease_tags or [],
        'sample_size': dataset.sample_size,
        'annotation_format': dataset.annotation_format,
        'access_status': dataset.access_status,
        'priority': dataset.priority,
        'notes': dataset.notes,
        'created_at': dataset.created_at.isoformat(),
        'updated_at': dataset.updated_at.isoformat(),
    }


def get_dataset_or_404(db: Session, dataset_id: str) -> DatasetCatalogRecord:
    dataset = db.get(DatasetCatalogRecord, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail='未找到对应数据集登记')
    return dataset


def create_dataset(db: Session, payload: DatasetCatalogCreateRequest) -> DatasetCatalogRecord:
    dataset = DatasetCatalogRecord(**payload.model_dump())
    db.add(dataset)
    return dataset


def update_dataset(db: Session, dataset_id: str, payload: DatasetCatalogUpdateRequest) -> DatasetCatalogRecord:
    dataset = get_dataset_or_404(db, dataset_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(dataset, key, value)
    dataset.updated_at = now_utc()
    return dataset


def list_datasets(
    db: Session,
    *,
    keyword: str | None,
    task_type: str | None,
    disease: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    statement = select(DatasetCatalogRecord).order_by(DatasetCatalogRecord.priority.asc(), DatasetCatalogRecord.updated_at.desc())
    count_statement = select(func.count()).select_from(DatasetCatalogRecord)

    conditions = []
    if keyword:
        keyword_condition = or_(
            DatasetCatalogRecord.name.ilike(f'%{keyword}%'),
            DatasetCatalogRecord.source_name.ilike(f'%{keyword}%'),
            DatasetCatalogRecord.notes.ilike(f'%{keyword}%'),
        )
        conditions.append(keyword_condition)
    if task_type:
        conditions.append(cast(DatasetCatalogRecord.task_types, String).ilike(f'%{task_type}%'))
    if disease:
        conditions.append(cast(DatasetCatalogRecord.disease_tags, String).ilike(f'%{disease}%'))

    for condition in conditions:
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

    total = db.scalar(count_statement) or 0
    rows = db.execute(statement.offset(offset).limit(limit)).scalars().all()
    return [serialize_dataset(row) for row in rows], total


def seed_public_datasets(db: Session) -> tuple[int, int]:
    created = 0
    skipped = 0
    for item in PUBLIC_DATASET_SEEDS:
        existing = db.execute(select(DatasetCatalogRecord).where(DatasetCatalogRecord.name == item['name'])).scalar_one_or_none()
        if existing is not None:
            skipped += 1
            continue
        db.add(DatasetCatalogRecord(**item))
        created += 1
    return created, skipped


def get_dataset_summary(db: Session) -> dict[str, int]:
    datasets = db.execute(select(DatasetCatalogRecord)).scalars().all()
    disease_tags = {tag for dataset in datasets for tag in (dataset.disease_tags or [])}
    open_count = sum(1 for dataset in datasets if dataset.access_status in {'open', 'open_reference', 'open_registration'})
    return {
        'dataset_count': len(datasets),
        'open_dataset_count': open_count,
        'covered_disease_count': len(disease_tags),
    }
