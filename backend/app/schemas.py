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
