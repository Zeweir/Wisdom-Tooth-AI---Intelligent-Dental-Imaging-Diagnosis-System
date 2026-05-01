from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

from app.config import YOLO_CLASS_MAP_JSON, YOLO_CONF_THRESHOLD, YOLO_DEVICE, YOLO_ENABLED, YOLO_IMAGE_SIZE, YOLO_MODEL_PATH


class YoloError(RuntimeError):
    pass


@dataclass(frozen=True)
class YoloAnalysisResult:
    detections: list[dict[str, Any]]
    model: str


def is_yolo_enabled() -> bool:
    return YOLO_ENABLED and bool(YOLO_MODEL_PATH) and Path(YOLO_MODEL_PATH).exists()


def _load_class_map() -> dict[str, Any]:
    if not YOLO_CLASS_MAP_JSON:
        return {}
    try:
        parsed = json.loads(YOLO_CLASS_MAP_JSON)
    except json.JSONDecodeError as exc:
        raise YoloError(f'YOLO_CLASS_MAP_JSON is invalid JSON: {exc}') from exc
    if not isinstance(parsed, dict):
        raise YoloError('YOLO_CLASS_MAP_JSON must be a JSON object')
    return parsed


@lru_cache(maxsize=1)
def _load_model() -> Any:
    if not is_yolo_enabled():
        raise YoloError('YOLO is disabled or YOLO_MODEL_PATH does not exist')
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise YoloError('ultralytics is not installed') from exc
    try:
        return YOLO(YOLO_MODEL_PATH)
    except Exception as exc:  # noqa: BLE001
        raise YoloError(f'Unable to load YOLO model: {exc}') from exc


def _normalize_class_metadata(class_key: str, raw_label: str, class_map: dict[str, Any]) -> tuple[str, str, str]:
    mapped = class_map.get(class_key, class_map.get(raw_label, raw_label))
    if isinstance(mapped, dict):
        label = str(mapped.get('class') or mapped.get('label') or raw_label)
        severity = str(mapped.get('severity') or '待确认')
        tooth_id = str(mapped.get('tooth_id') or '未知牙位')
        return label, severity, tooth_id
    return str(mapped), '待确认', '未知牙位'


def run_yolo_analysis(*, image_bytes: bytes, filename: str) -> YoloAnalysisResult:
    if not image_bytes:
        raise YoloError('image bytes are empty')
    if not is_yolo_enabled():
        raise YoloError('YOLO is disabled or YOLO_MODEL_PATH does not exist')

    try:
        from PIL import Image

        image = Image.open(BytesIO(image_bytes)).convert('RGB')
    except ImportError as exc:
        raise YoloError('Pillow is not installed') from exc
    except Exception as exc:  # noqa: BLE001
        raise YoloError(f'Unable to open image for YOLO inference: {exc}') from exc

    model = _load_model()
    class_map = _load_class_map()
    predict_kwargs: dict[str, Any] = {
        'source': image,
        'conf': YOLO_CONF_THRESHOLD,
        'imgsz': YOLO_IMAGE_SIZE,
        'verbose': False,
    }
    if YOLO_DEVICE:
        predict_kwargs['device'] = YOLO_DEVICE

    try:
        results = model.predict(**predict_kwargs)
    except Exception as exc:  # noqa: BLE001
        raise YoloError(f'YOLO inference failed for {filename}: {exc}') from exc

    detections: list[dict[str, Any]] = []
    names = getattr(model, 'names', {}) or {}
    for result in results:
        boxes = getattr(result, 'boxes', None)
        if boxes is None:
            continue
        for box in boxes:
            xyxy = getattr(box, 'xyxy', None)
            cls_value = getattr(box, 'cls', None)
            conf_value = getattr(box, 'conf', None)
            if xyxy is None or cls_value is None or conf_value is None:
                continue
            coords = xyxy[0].tolist()
            class_index = int(cls_value[0].item())
            confidence = float(conf_value[0].item())
            raw_label = str(names.get(class_index, class_index))
            label, severity, tooth_id = _normalize_class_metadata(str(class_index), raw_label, class_map)
            detections.append(
                {
                    'bbox': [int(round(value)) for value in coords[:4]],
                    'class': label,
                    'confidence': min(1.0, max(0.0, confidence)),
                    'severity': severity,
                    'tooth_id': tooth_id,
                }
            )

    return YoloAnalysisResult(detections=detections, model=YOLO_MODEL_PATH)
