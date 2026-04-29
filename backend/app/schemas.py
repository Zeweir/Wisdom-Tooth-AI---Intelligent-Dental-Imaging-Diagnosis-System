from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ImageType = Literal['panoramic', 'periapical', 'cbct']
ReportStatus = Literal['processing', 'ai_generated', 'doctor_reviewed', 'finalized']


class Detection(BaseModel):
    bbox: list[int]
    class_: str = Field(alias='class')
    confidence: float
    severity: str
    tooth_id: str

    model_config = {
        'populate_by_name': True,
    }


class ReportPayload(BaseModel):
    report_id: str
    content: str
    doctor_review: str | None
    status: ReportStatus


class PatientSummaryPayload(BaseModel):
    patient_id: str
    name: str
    gender: str | None
    age: int | None
    phone: str | None


class PaginationMeta(BaseModel):
    limit: int
    offset: int
    total: int


class AnalysisPayload(BaseModel):
    image_id: str
    patient_id: str
    image_type: ImageType
    filename: str
    file_path: str
    image_url: str
    status: str
    detections: list[dict[str, Any]]
    segmentation_url: str | None
    patient: PatientSummaryPayload | None = None
    report: ReportPayload
    created_at: datetime
    updated_at: datetime


class AnalysisListResponse(BaseModel):
    code: int
    data: list[AnalysisPayload]
    meta: PaginationMeta


class AnalysisResponse(BaseModel):
    code: int
    data: AnalysisPayload


class UploadResponse(BaseModel):
    image_id: str
    status: str
    message: str


class UploadApiResponse(BaseModel):
    code: int
    data: UploadResponse


class ReportReviewRequest(BaseModel):
    doctor_review: str
    modified_findings: list[dict[str, Any]] = Field(default_factory=list)
    status: Literal['doctor_reviewed', 'finalized'] = 'doctor_reviewed'


class ReportReviewResponseData(BaseModel):
    report_id: str
    status: str
    doctor_review: str | None
    detections: list[dict[str, Any]]


class ReportReviewResponse(BaseModel):
    code: int
    data: ReportReviewResponseData


class AuditLogPayload(BaseModel):
    audit_log_id: str
    actor_sub: str
    actor_client_id: str | None
    actor_organization_id: str | None
    actor_roles: list[str]
    action: str
    resource_type: str
    resource_id: str
    detail: dict[str, Any]
    created_at: datetime


class AuditLogListResponse(BaseModel):
    code: int
    data: list[AuditLogPayload]
    meta: PaginationMeta


class DashboardSummaryPayload(BaseModel):
    total_images: int
    total_patients: int = 0
    recent_patients: int = 0
    pending_review_cases: int = 0
    dataset_count: int = 0
    open_dataset_count: int = 0
    covered_disease_count: int = 0
    processing_images: int
    completed_images: int
    detection_count: int
    average_confidence: float
    report_status_counts: dict[str, int]
    image_type_counts: dict[str, int]
    audit_event_count: int
    latest_case: AnalysisPayload | None


class DashboardSummaryResponse(BaseModel):
    code: int
    data: DashboardSummaryPayload


class PatientPayload(PatientSummaryPayload):
    notes: str | None
    image_count: int = 0
    latest_image_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PatientListResponse(BaseModel):
    code: int
    data: list[PatientPayload]
    meta: PaginationMeta


class PatientResponse(BaseModel):
    code: int
    data: PatientPayload


class PatientCreateRequest(BaseModel):
    patient_id: str
    name: str
    gender: str | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    phone: str | None = None
    notes: str | None = None


class PatientUpdateRequest(BaseModel):
    name: str | None = None
    gender: str | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    phone: str | None = None
    notes: str | None = None


class DatasetCatalogPayload(BaseModel):
    dataset_id: str
    name: str
    source_name: str
    homepage_url: str
    paper_url: str | None
    license: str | None
    image_type: str
    task_types: list[str]
    disease_tags: list[str]
    sample_size: str | None
    annotation_format: str | None
    access_status: str
    priority: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class DatasetCatalogListResponse(BaseModel):
    code: int
    data: list[DatasetCatalogPayload]
    meta: PaginationMeta


class DatasetCatalogResponse(BaseModel):
    code: int
    data: DatasetCatalogPayload


class DatasetSeedResponse(BaseModel):
    code: int
    data: dict[str, int]


class DatasetCatalogCreateRequest(BaseModel):
    name: str
    source_name: str
    homepage_url: str
    paper_url: str | None = None
    license: str | None = None
    image_type: str = 'panoramic'
    task_types: list[str] = Field(default_factory=list)
    disease_tags: list[str] = Field(default_factory=list)
    sample_size: str | None = None
    annotation_format: str | None = None
    access_status: str = 'open'
    priority: str = 'medium'
    notes: str | None = None


class DatasetCatalogUpdateRequest(BaseModel):
    name: str | None = None
    source_name: str | None = None
    homepage_url: str | None = None
    paper_url: str | None = None
    license: str | None = None
    image_type: str | None = None
    task_types: list[str] | None = None
    disease_tags: list[str] | None = None
    sample_size: str | None = None
    annotation_format: str | None = None
    access_status: str | None = None
    priority: str | None = None
    notes: str | None = None
