from __future__ import annotations

from typing import Any


IMAGE_TYPE_LABELS = {
    'panoramic': '全景片',
    'periapical': '根尖片',
    'cbct': 'CBCT',
}

TOOTH_CONFIDENCE_LABELS = {
    'model_mapped': '模型牙位',
    'layout_inferred': '推测牙位',
    'unknown': '局部区域',
}

EXPLANATION_LIBRARY = [
    {
        'match': ('智齿阻生', '阻生'),
        'finding_label': '阻生智齿',
        'clinical_meaning': '疑似智齿萌出受阻，可能影响邻牙、牙龈软组织或局部清洁维护。',
        'risk_hint': '若伴随反复冠周炎、邻牙龋坏或局部疼痛，后续处理优先级较高。',
        'recommendation': '建议结合临床检查评估拔除指征，必要时补充 CBCT 观察牙根与下牙槽神经关系。',
        'evidence_summary': 'AI 在目标牙位区域识别到阻生形态、邻近结构拥挤或萌出受限表现。',
        'follow_up_exam': ['CBCT', '阻生牙位临床检查'],
    },
    {
        'match': ('龋', '龋坏'),
        'finding_label': '龋坏',
        'clinical_meaning': '提示牙体硬组织存在密度异常，需结合临床探诊判断龋坏深度及范围。',
        'risk_hint': '若累及牙本质或接近髓腔，可能增加疼痛、继发感染和治疗复杂度。',
        'recommendation': '建议尽快进行临床复核，必要时补充咬翼片或根尖片后决定充填或进一步治疗。',
        'evidence_summary': 'AI 识别到局部低密度影、牙体连续性受损或邻面可疑透射改变。',
        'follow_up_exam': ['咬翼片', '根尖片', '龋坏探诊'],
    },
    {
        'match': ('根尖周炎', '根尖病变', '根尖透射影', '根尖'),
        'finding_label': '根尖区异常',
        'clinical_meaning': '提示根尖区可能存在慢性炎症、透射影扩大或根尖周骨质改变。',
        'risk_hint': '若患者伴随叩痛、自发痛或既往根管治疗史，应优先排查感染活动性。',
        'recommendation': '建议结合活力测试、临床症状和必要时追加根尖片，评估是否需要根管治疗或再治疗。',
        'evidence_summary': 'AI 在根尖周围识别到边界异常、透射影增大或局部骨小梁稀疏表现。',
        'follow_up_exam': ['根尖片', '牙髓活力测试'],
    },
    {
        'match': ('牙槽骨吸收', '牙周', '骨吸收'),
        'finding_label': '牙周支持组织异常',
        'clinical_meaning': '提示牙槽骨高度下降或牙周支持组织受损，需要结合牙周检查综合判断。',
        'risk_hint': '若吸收范围广或伴牙齿松动，可能影响长期保存价值。',
        'recommendation': '建议补充牙周探诊、口腔卫生评估，并根据分期决定基础治疗或专科转诊。',
        'evidence_summary': 'AI 识别到牙槽嵴高度下降、骨小梁形态异常或牙周支持组织改变。',
        'follow_up_exam': ['牙周探诊', '口腔卫生评估'],
    },
    {
        'match': ('冠周炎',),
        'finding_label': '冠周炎倾向',
        'clinical_meaning': '提示阻生牙或半萌出牙周围软硬组织存在炎症相关风险，需要结合症状确认。',
        'risk_hint': '若伴局部肿胀、张口受限或疼痛，建议优先处理。',
        'recommendation': '建议结合临床软组织检查，必要时先处理急性炎症，再评估拔除时机。',
        'evidence_summary': 'AI 结合阻生位置与周围结构关系，提示冠周软组织区域存在风险。',
        'follow_up_exam': ['软组织检查', '阻生牙位临床检查'],
    },
    {
        'match': ('缺失牙', '缺牙'),
        'finding_label': '缺失牙',
        'clinical_meaning': '提示目标区域可能存在牙体缺失或牙位空缺，需要结合病史区分拔除后状态与未萌出情况。',
        'risk_hint': '需注意邻牙倾斜、对颌伸长及后续修复空间。',
        'recommendation': '建议结合病史与口内检查，必要时评估修复或种植方案。',
        'evidence_summary': 'AI 在预期牙位区域未识别到完整牙体轮廓，提示存在缺失可能。',
        'follow_up_exam': ['口内检查', '修复评估'],
    },
    {
        'match': ('充填体', '修复体', '邻面可疑'),
        'finding_label': '修复体邻面可疑异常',
        'clinical_meaning': '提示既往修复体邻面或边缘区域可能存在继发龋或边缘不密合风险。',
        'risk_hint': '若伴边缘染色、食物嵌塞或冷热敏感，应提高关注。',
        'recommendation': '建议结合口内探诊和近远中接触区检查，必要时补充咬翼片。',
        'evidence_summary': 'AI 在修复体边缘附近识别到可疑透射异常或边缘连续性问题。',
        'follow_up_exam': ['咬翼片', '修复体边缘检查'],
    },
]


def get_image_type_label(image_type: str) -> str:
    return IMAGE_TYPE_LABELS.get(image_type, image_type)


def get_tooth_confidence_label(source: str) -> str:
    return TOOTH_CONFIDENCE_LABELS.get(source, source)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_unknown_tooth_id(value: str) -> bool:
    normalized = value.strip()
    return normalized in {'', '未知牙位', 'unknown', '局部区域异常'}


def _classify_panoramic_fdi(tooth_box: list[int], *, image_width: int | None = None, image_height: int | None = None) -> str:
    x1, y1, x2, y2 = tooth_box[:4]
    estimated_width = image_width or (3072 if x2 > 2200 else 2048 if x2 > 1200 else 1024)
    estimated_height = image_height or (1536 if y2 > 1200 else 1024)
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    normalized_x = max(0.0, min(1.0, center_x / max(estimated_width, 1)))
    normalized_y = max(0.0, min(1.0, center_y / max(estimated_height, 1)))
    index = min(7, max(0, int(normalized_x * 8)))

    if normalized_y <= 0.5:
        left_half = normalized_x <= 0.5
        number = 8 - index if left_half else index + 1
        quadrant = '1' if left_half else '2'
    else:
        left_half = normalized_x <= 0.5
        number = 8 - index if left_half else index + 1
        quadrant = '4' if left_half else '3'
    return f'{quadrant}{max(1, min(8, number))}'


def infer_tooth_position(
    image_type: str,
    bbox: list[int],
    tooth_id: str,
    *,
    image_width: int | None = None,
    image_height: int | None = None,
) -> tuple[str, str]:
    clean_tooth_id = tooth_id.strip()
    if clean_tooth_id.startswith('CBCT-ROI'):
        return clean_tooth_id, 'unknown'
    if not _is_unknown_tooth_id(clean_tooth_id):
        return clean_tooth_id, 'model_mapped'
    if image_type == 'panoramic' and len(bbox) >= 4:
        return _classify_panoramic_fdi(bbox, image_width=image_width, image_height=image_height), 'layout_inferred'
    return '局部区域异常', 'unknown'


def _match_explanation_template(finding_class: str) -> dict[str, Any] | None:
    for template in EXPLANATION_LIBRARY:
        if any(keyword in finding_class for keyword in template['match']):
            return template
    return None


def build_detection_explanation(image_type: str, detection: dict[str, Any]) -> dict[str, Any]:
    finding_class = str(detection.get('class', '待确认病灶'))
    matched_template = _match_explanation_template(finding_class)
    severity = str(detection.get('severity', '待确认'))
    confidence = _safe_float(detection.get('confidence', 0.0))
    raw_tooth_id = str(detection.get('tooth_id', '未知牙位'))
    bbox = detection.get('bbox', [0, 0, 0, 0])
    image_width = int(_safe_float(detection.get('image_width', 0), 0)) or None
    image_height = int(_safe_float(detection.get('image_height', 0), 0)) or None
    tooth_display_name, tooth_confidence_source = infer_tooth_position(
        image_type,
        bbox,
        raw_tooth_id,
        image_width=image_width,
        image_height=image_height,
    )
    tooth_id = tooth_display_name if tooth_confidence_source != 'model_mapped' else raw_tooth_id.strip()
    finding_label = matched_template['finding_label'] if matched_template else finding_class
    clinical_meaning = (
        matched_template['clinical_meaning']
        if matched_template
        else f'{get_image_type_label(image_type)}中该区域存在需要医生复核的影像学异常表现。'
    )
    risk_hint = (
        matched_template['risk_hint']
        if matched_template
        else '请结合患者症状、既往病史和局部检查综合评估风险等级。'
    )
    recommendation = (
        matched_template['recommendation']
        if matched_template
        else '建议由医生结合临床检查确认问题性质，并决定是否需要追加影像或处理。'
    )
    evidence_summary = (
        matched_template['evidence_summary']
        if matched_template
        else f'AI 在 {tooth_display_name} 附近识别到 {finding_class} 的可疑影像征象。'
    )
    follow_up_exam = list(matched_template.get('follow_up_exam', [])) if matched_template else [get_image_type_label(image_type) + '复核']
    source_prefix = '推测牙位。' if tooth_confidence_source == 'layout_inferred' else '局部区域定位。' if tooth_confidence_source == 'unknown' else ''
    return {
        'tooth_id': tooth_id,
        'tooth_display_name': tooth_display_name,
        'tooth_confidence_source': tooth_confidence_source,
        'bbox': detection.get('bbox', [0, 0, 0, 0]),
        'class': detection.get('class', '待确认病灶'),
        'confidence': confidence,
        'severity': severity,
        'finding_label': finding_label,
        'clinical_meaning': clinical_meaning,
        'risk_hint': risk_hint,
        'recommendation': recommendation,
        'evidence_summary': f"{source_prefix}{evidence_summary} 当前严重程度判断为“{severity}”，置信度约 {confidence:.0%}。",
        'follow_up_exam': follow_up_exam,
    }


def enrich_detections(image_type: str, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [build_detection_explanation(image_type, detection) for detection in detections]


def _sort_tooth_key(item: dict[str, Any]) -> tuple[int, str]:
    tooth_id = str(item.get('tooth_id', ''))
    if tooth_id.isdigit():
        return (0, tooth_id.zfill(2))
    return (1, tooth_id)


def build_tooth_findings(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in sorted(detections, key=_sort_tooth_key):
        tooth_display_name = str(item.get('tooth_display_name') or item.get('tooth_id') or '局部区域异常')
        group = grouped.setdefault(
            tooth_display_name,
            {
                'tooth_id': str(item.get('tooth_id', tooth_display_name)),
                'display_name': tooth_display_name,
                'source': str(item.get('tooth_confidence_source', 'unknown')),
                'findings': [],
            },
        )
        group['findings'].append(
            {
                'finding_label': str(item.get('finding_label') or item.get('class') or '待确认病灶'),
                'severity': str(item.get('severity', '待确认')),
                'confidence': _safe_float(item.get('confidence', 0.0)),
                'clinical_meaning': str(item.get('clinical_meaning', '')),
                'risk_hint': str(item.get('risk_hint', '')),
                'recommendation': str(item.get('recommendation', '')),
                'evidence_summary': str(item.get('evidence_summary', '')),
                'follow_up_exam': [str(entry) for entry in item.get('follow_up_exam', []) if str(entry).strip()],
            }
        )
    return list(grouped.values())


def build_structured_report(
    *,
    patient_id: str,
    image_type: str,
    detections: list[dict[str, Any]],
    doctor_review: str | None = None,
) -> dict[str, Any]:
    image_type_label = get_image_type_label(image_type)
    if not detections:
        return {
            'summary': f'患者 {patient_id} 的{image_type_label}未见明确高置信度异常，建议结合主诉常规复查。',
            'key_findings': ['当前未检出明确高置信度病灶。'],
            'doctor_notes': doctor_review or '',
            'follow_up_plan': [
                '结合口内检查、症状和既往史做常规评估。',
                '如临床仍有疑点，可追加更合适的影像检查。',
            ],
            'high_priority_findings': [],
            'tooth_findings': [],
        }

    key_findings = [
        f"{item['tooth_display_name']}：{item['finding_label']}，严重程度 {item['severity']}，置信度 {item['confidence']:.0%}"
        for item in detections
    ]
    high_priority_findings = [
        item['finding_label']
        for item in detections
        if '高' in str(item['risk_hint']) or '优先' in str(item['recommendation']) or '高' in str(item['severity'])
    ]
    follow_up_plan: list[str] = []
    for item in detections:
        recommendation = str(item.get('recommendation', '')).strip()
        if recommendation and recommendation not in follow_up_plan:
            follow_up_plan.append(recommendation)
        for exam in item.get('follow_up_exam', []):
            exam_text = f'建议补充 {exam}'
            if exam_text not in follow_up_plan:
                follow_up_plan.append(exam_text)

    summary_prefix = '已检出需要优先关注的影像学问题。' if high_priority_findings else '已检出疑似病灶，建议医生结合临床复核。'
    return {
        'summary': f'患者 {patient_id} 的{image_type_label}已完成 AI 分析。{summary_prefix}',
        'key_findings': key_findings,
        'doctor_notes': doctor_review or '',
        'follow_up_plan': follow_up_plan[:6],
        'high_priority_findings': high_priority_findings,
        'tooth_findings': build_tooth_findings(detections),
    }


def normalize_structured_report_payload(structured_report: dict[str, Any] | None) -> dict[str, Any]:
    payload = structured_report or {}
    normalized_tooth_findings = []
    for item in payload.get('tooth_findings', []):
        if not isinstance(item, dict):
            continue
        normalized_findings = []
        for finding in item.get('findings', []):
            if not isinstance(finding, dict):
                continue
            normalized_findings.append(
                {
                    'finding_label': str(finding.get('finding_label', '')).strip(),
                    'severity': str(finding.get('severity', '')).strip(),
                    'confidence': _safe_float(finding.get('confidence', 0.0)),
                    'clinical_meaning': str(finding.get('clinical_meaning', '')).strip(),
                    'risk_hint': str(finding.get('risk_hint', '')).strip(),
                    'recommendation': str(finding.get('recommendation', '')).strip(),
                    'evidence_summary': str(finding.get('evidence_summary', '')).strip(),
                    'follow_up_exam': [str(entry) for entry in finding.get('follow_up_exam', []) if str(entry).strip()],
                }
            )
        normalized_tooth_findings.append(
            {
                'tooth_id': str(item.get('tooth_id', '')).strip(),
                'display_name': str(item.get('display_name', '')).strip(),
                'source': str(item.get('source', 'unknown')).strip() or 'unknown',
                'findings': normalized_findings,
            }
        )

    return {
        'summary': str(payload.get('summary', '')).strip(),
        'key_findings': [str(item) for item in payload.get('key_findings', []) if str(item).strip()],
        'doctor_notes': str(payload.get('doctor_notes', '')).strip(),
        'follow_up_plan': [str(item) for item in payload.get('follow_up_plan', []) if str(item).strip()],
        'high_priority_findings': [str(item) for item in payload.get('high_priority_findings', []) if str(item).strip()],
        'tooth_findings': normalized_tooth_findings,
    }


def build_report_content_from_structured_report(structured_report: dict[str, Any]) -> str:
    normalized = normalize_structured_report_payload(structured_report)
    summary = normalized['summary']
    key_findings = normalized['key_findings']
    follow_up_plan = normalized['follow_up_plan']
    doctor_notes = normalized['doctor_notes']
    parts = [summary] if summary else []
    if key_findings:
        parts.append('影像提示：' + '；'.join(str(item) for item in key_findings))
    if follow_up_plan:
        parts.append('处理建议：' + '；'.join(str(item) for item in follow_up_plan))
    if doctor_notes:
        parts.append('医生备注：' + doctor_notes)
    return ' '.join(part for part in parts if part)
