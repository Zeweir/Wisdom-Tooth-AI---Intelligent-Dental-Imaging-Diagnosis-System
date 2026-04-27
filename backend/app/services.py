from datetime import datetime, timezone
from typing import Any

from app.models import ImageRecord, ReportRecord
from app.schemas import ImageType


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def build_mock_detections(image_type: ImageType) -> list[dict[str, Any]]:
    if image_type == 'panoramic':
        return [
            {
                'bbox': [240, 180, 335, 290],
                'class': '智齿阻生',
                'confidence': 0.96,
                'severity': '近中阻生',
                'tooth_id': '38',
            },
            {
                'bbox': [120, 150, 200, 245],
                'class': '龋齿',
                'confidence': 0.91,
                'severity': '中龋',
                'tooth_id': '36',
            },
        ]
    if image_type == 'periapical':
        return [
            {
                'bbox': [88, 64, 180, 152],
                'class': '根尖周炎',
                'confidence': 0.89,
                'severity': '慢性',
                'tooth_id': '26',
            }
        ]
    return [
        {
            'bbox': [48, 48, 192, 192],
            'class': '牙槽骨吸收',
            'confidence': 0.87,
            'severity': '中度',
            'tooth_id': 'CBCT-ROI-01',
        }
    ]


def build_report_content(patient_id: str, image_type: ImageType, detections: list[dict[str, Any]]) -> str:
    findings = '；'.join(
        f"牙位{item['tooth_id']}提示{item['class']}（{item['severity']}，置信度{item['confidence']:.0%}）"
        for item in detections
    )
    return (
        f'患者 {patient_id} 的{image_type}影像已完成初步分析。'
        f'影像描述：{findings}。'
        '诊断意见：当前结果为AI辅助判断，建议结合临床检查与病史综合评估。'
        '治疗建议：优先处理高风险病灶，并由医生审核后形成正式报告。'
    )


def serialize_analysis(image: ImageRecord) -> dict[str, Any]:
    if image.report is None:
        raise ValueError('image report relation must exist')

    return {
        'image_id': image.image_id,
        'patient_id': image.patient_id,
        'image_type': image.image_type,
        'filename': image.filename,
        'file_path': image.file_path,
        'image_url': f'/api/v1/images/{image.image_id}/file',
        'status': image.status,
        'detections': image.detections,
        'segmentation_url': image.segmentation_url,
        'report': {
            'report_id': image.report.report_id,
            'content': image.report.content,
            'doctor_review': image.report.doctor_review,
            'status': image.report.status,
        },
        'created_at': image.created_at.isoformat(),
        'updated_at': image.updated_at.isoformat(),
    }


def build_pending_report_content(patient_id: str, image_type: ImageType) -> str:
    return f'患者 {patient_id} 的{image_type}影像已上传，AI 正在分析中，请稍候查看结果。'


def build_image_record(patient_id: str, image_type: ImageType, filename: str, stored_path: str) -> ImageRecord:
    image = ImageRecord(
        patient_id=patient_id,
        image_type=image_type,
        filename=filename,
        file_path=stored_path,
        status='processing',
        detections=[],
        segmentation_url=None,
    )
    image.report = ReportRecord(
        content=build_pending_report_content(patient_id, image_type),
        doctor_review=None,
        status='processing',
    )
    return image


def finalize_image_record(image: ImageRecord) -> None:
    detections = build_mock_detections(image.image_type)
    image.status = 'completed'
    image.detections = detections
    image.segmentation_url = None
    if image.report is None:
        image.report = ReportRecord(
            content='',
            doctor_review=None,
            status='processing',
        )
    image.report.content = build_report_content(image.patient_id, image.image_type, detections)
    image.report.status = 'ai_generated'
