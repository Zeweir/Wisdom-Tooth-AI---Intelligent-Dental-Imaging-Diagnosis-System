from datetime import datetime, timezone
from typing import Any

from app.models import ImageRecord, ReportRecord
from app.ollama import OllamaError, generate_multimodal_analysis, is_ollama_enabled
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


def normalize_detection_payload(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in detections:
        bbox_value = item.get('bbox', [0, 0, 0, 0])
        if not isinstance(bbox_value, list):
            bbox_value = [0, 0, 0, 0]
        bbox = []
        for value in bbox_value[:4]:
            try:
                bbox.append(int(float(value)))
            except (TypeError, ValueError):
                bbox.append(0)
        while len(bbox) < 4:
            bbox.append(0)

        try:
            confidence = float(item.get('confidence', 0.5))
        except (TypeError, ValueError):
            confidence = 0.5

        normalized.append(
            {
                'bbox': bbox,
                'class': str(item.get('class', '待确认病灶')),
                'confidence': min(1.0, max(0.0, confidence)),
                'severity': str(item.get('severity', '待确认')),
                'tooth_id': str(item.get('tooth_id', '未知牙位')),
            }
        )
    return normalized


def build_fallback_analysis(image: ImageRecord) -> dict[str, Any]:
    detections = build_mock_detections(image.image_type)
    return {
        'detections': detections,
        'report': build_report_content(image.patient_id, image.image_type, detections),
        'summary': '使用内置规则生成的兜底分析结果。',
        'source': 'mock_fallback',
        'model': None,
        'error': None,
    }


def generate_analysis_result(image: ImageRecord, image_bytes: bytes | None) -> dict[str, Any]:
    fallback = build_fallback_analysis(image)
    if not image_bytes or not is_ollama_enabled():
        return fallback

    try:
        ollama_result = generate_multimodal_analysis(
            image_bytes=image_bytes,
            patient_id=image.patient_id,
            image_type=image.image_type,
            filename=image.filename,
        )
    except OllamaError as exc:
        fallback['error'] = str(exc)
        return fallback

    detections = normalize_detection_payload(ollama_result.detections)
    if not detections:
        detections = fallback['detections']

    report = ollama_result.report.strip() or build_report_content(image.patient_id, image.image_type, detections)
    return {
        'detections': detections,
        'report': report,
        'summary': ollama_result.summary,
        'source': 'ollama',
        'model': ollama_result.model,
        'error': None,
    }


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


def build_dashboard_summary(images: list[ImageRecord], audit_count: int) -> dict[str, Any]:
    report_status_counts = {
        'processing': 0,
        'ai_generated': 0,
        'doctor_reviewed': 0,
        'finalized': 0,
    }
    image_type_counts = {
        'panoramic': 0,
        'periapical': 0,
        'cbct': 0,
    }
    detection_count = 0
    confidence_total = 0.0
    confidence_count = 0

    for image in images:
        image_type_counts[image.image_type] = image_type_counts.get(image.image_type, 0) + 1
        if image.report is not None:
            report_status_counts[image.report.status] = report_status_counts.get(image.report.status, 0) + 1
        for detection in image.detections or []:
            detection_count += 1
            try:
                confidence_total += float(detection.get('confidence', 0))
                confidence_count += 1
            except (TypeError, ValueError):
                continue

    latest_image = images[0] if images else None
    return {
        'total_images': len(images),
        'processing_images': sum(1 for image in images if image.status == 'processing'),
        'completed_images': sum(1 for image in images if image.status == 'completed'),
        'detection_count': detection_count,
        'average_confidence': round(confidence_total / confidence_count, 4) if confidence_count else 0,
        'report_status_counts': report_status_counts,
        'image_type_counts': image_type_counts,
        'audit_event_count': audit_count,
        'latest_case': serialize_analysis(latest_image) if latest_image and latest_image.report else None,
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


def finalize_image_record(image: ImageRecord, *, image_bytes: bytes | None = None) -> dict[str, Any]:
    analysis_result = generate_analysis_result(image, image_bytes)
    detections = analysis_result['detections']
    image.status = 'completed'
    image.detections = detections
    image.segmentation_url = None
    if image.report is None:
        image.report = ReportRecord(
            content='',
            doctor_review=None,
            status='processing',
        )
    image.report.content = analysis_result['report']
    image.report.status = 'ai_generated'
    return analysis_result
