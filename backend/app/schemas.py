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


class UploadResponse(BaseModel):
    image_id: str
    status: str
    message: str


class ReportReviewRequest(BaseModel):
    doctor_review: str
    modified_findings: list[dict[str, Any]] = Field(default_factory=list)
    status: Literal['doctor_reviewed', 'finalized'] = 'doctor_reviewed'
