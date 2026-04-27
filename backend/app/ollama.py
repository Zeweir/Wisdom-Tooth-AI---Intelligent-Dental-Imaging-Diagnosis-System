from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any
from urllib import request
from urllib.error import HTTPError, URLError

from app.config import OLLAMA_BASE_URL, OLLAMA_ENABLED, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS


class OllamaError(RuntimeError):
    pass


@dataclass(frozen=True)
class OllamaAnalysisResult:
    detections: list[dict[str, Any]]
    report: str
    summary: str
    raw_content: str
    model: str


_SYSTEM_PROMPT = (
    'You are an experienced dental imaging assistant. '
    'Analyze the uploaded dental image and return strict JSON only. '
    'The JSON must contain keys summary, report, detections. '
    'detections must be a list of objects with keys tooth_id, class, severity, confidence, bbox. '
    'confidence must be a number between 0 and 1. '
    'bbox must be an array of four integers in the range 0-1024. '
    'If uncertain, return your best medical estimate but keep JSON valid and concise.'
)


_USER_PROMPT_TEMPLATE = (
    'Patient ID: {patient_id}. '
    'Image type: {image_type}. '
    'Filename: {filename}. '
    'Return diagnostic findings for wisdom tooth and surrounding dental conditions. '
    'Write the report in Chinese for a clinician. '
    'Do not use markdown fences.'
)


def is_ollama_enabled() -> bool:
    return OLLAMA_ENABLED and bool(OLLAMA_BASE_URL) and bool(OLLAMA_MODEL)


def _extract_json_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get('message'), dict) and isinstance(payload['message'].get('content'), str):
        return payload['message']['content']
    if isinstance(payload.get('response'), str):
        return payload['response']
    raise OllamaError('Ollama response does not contain a text payload')


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith('```'):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = '\n'.join(lines[1:-1]).strip()
    return cleaned


def _normalize_detection(item: dict[str, Any]) -> dict[str, Any] | None:
    tooth_id = str(item.get('tooth_id', '')).strip()
    finding_class = str(item.get('class', '')).strip()
    severity = str(item.get('severity', '')).strip() or '待确认'
    bbox_value = item.get('bbox', [])
    confidence_value = item.get('confidence', 0.5)

    if not tooth_id or not finding_class:
        return None

    if not isinstance(bbox_value, list):
        bbox_value = []
    bbox = []
    for value in bbox_value[:4]:
        try:
            bbox.append(int(float(value)))
        except (TypeError, ValueError):
            bbox.append(0)
    while len(bbox) < 4:
        bbox.append(0)
    bbox = [min(1024, max(0, value)) for value in bbox]

    try:
        confidence = float(confidence_value)
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = min(1.0, max(0.0, confidence))

    return {
        'tooth_id': tooth_id,
        'class': finding_class,
        'severity': severity,
        'confidence': confidence,
        'bbox': bbox,
    }


def _parse_analysis_text(content: str) -> tuple[list[dict[str, Any]], str, str]:
    normalized_text = _strip_json_fences(content)
    try:
        parsed = json.loads(normalized_text)
    except json.JSONDecodeError as exc:
        raise OllamaError(f'Unable to parse Ollama JSON response: {exc}') from exc

    detections_payload = parsed.get('detections', [])
    detections: list[dict[str, Any]] = []
    if isinstance(detections_payload, list):
        for item in detections_payload:
            if not isinstance(item, dict):
                continue
            normalized = _normalize_detection(item)
            if normalized is not None:
                detections.append(normalized)

    summary = str(parsed.get('summary', '')).strip()
    report = str(parsed.get('report', '')).strip()
    if not report:
        raise OllamaError('Ollama response is missing report content')
    return detections, report, summary


def generate_multimodal_analysis(*, image_bytes: bytes, patient_id: str, image_type: str, filename: str) -> OllamaAnalysisResult:
    if not is_ollama_enabled():
        raise OllamaError('Ollama is disabled')

    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    payload = {
        'model': OLLAMA_MODEL,
        'stream': False,
        'format': 'json',
        'messages': [
            {
                'role': 'system',
                'content': _SYSTEM_PROMPT,
            },
            {
                'role': 'user',
                'content': _USER_PROMPT_TEMPLATE.format(
                    patient_id=patient_id,
                    image_type=image_type,
                    filename=filename,
                ),
                'images': [image_base64],
            },
        ],
        'options': {
            'temperature': 0.2,
        },
    }
    body = json.dumps(payload).encode('utf-8')
    req = request.Request(
        f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat",
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
            response_payload = json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        raise OllamaError(f'Ollama HTTP error: {exc.code}') from exc
    except URLError as exc:
        raise OllamaError(f'Ollama connection error: {exc.reason}') from exc
    except TimeoutError as exc:
        raise OllamaError('Ollama request timed out') from exc
    except json.JSONDecodeError as exc:
        raise OllamaError(f'Ollama returned invalid JSON: {exc}') from exc

    raw_content = _extract_json_text(response_payload)
    detections, report, summary = _parse_analysis_text(raw_content)
    return OllamaAnalysisResult(
        detections=detections,
        report=report,
        summary=summary,
        raw_content=raw_content,
        model=OLLAMA_MODEL,
    )
