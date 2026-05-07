from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.clinical_reports import get_image_type_label, get_tooth_confidence_label, normalize_structured_report_payload
from app.models import ReportRecord


pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))


def _styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        'title': ParagraphStyle(
            'ClinicalTitle',
            parent=styles['Title'],
            fontName='STSong-Light',
            fontSize=20,
            leading=26,
            textColor=colors.HexColor('#0E7490'),
            spaceAfter=10,
        ),
        'subtitle': ParagraphStyle(
            'ClinicalSubtitle',
            parent=styles['Normal'],
            fontName='STSong-Light',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=8,
        ),
        'heading': ParagraphStyle(
            'ClinicalHeading',
            parent=styles['Heading2'],
            fontName='STSong-Light',
            fontSize=14,
            leading=20,
            textColor=colors.HexColor('#164E63'),
            spaceAfter=6,
            spaceBefore=12,
        ),
        'body': ParagraphStyle(
            'ClinicalBody',
            parent=styles['BodyText'],
            fontName='STSong-Light',
            fontSize=10.5,
            leading=16,
            textColor=colors.HexColor('#0F172A'),
        ),
    }


def build_report_pdf_bytes(report: ReportRecord) -> bytes:
    if report.image is None:
        raise ValueError('report image relation must be loaded before generating PDF')

    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    structured = normalize_structured_report_payload(report.structured_content)
    patient_name = report.image.patient_id
    image_type_label = get_image_type_label(report.image.image_type)
    story: list[Any] = [
        Paragraph('智齿 AI 口腔影像辅助诊断报告', styles['title']),
        Paragraph('该 PDF 由系统自动生成，可用于审核、归档与下载。', styles['subtitle']),
    ]

    meta_table = Table(
        [
            ['患者编号', report.image.patient_id, '影像类型', image_type_label],
            ['影像文件', report.image.filename, '报告状态', report.status],
            ['患者标识', patient_name, 'PDF 类型', report.pdf_variant or 'ai_draft'],
        ],
        colWidths=[24 * mm, 62 * mm, 24 * mm, 62 * mm],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ('FONTNAME', (0, 0), (-1, -1), 'STSong-Light'),
                ('FONTSIZE', (0, 0), (-1, -1), 9.5),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#083344')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECFEFF')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BAE6FD')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([meta_table, Spacer(1, 8)])

    story.append(Paragraph('AI 诊断摘要', styles['heading']))
    story.append(Paragraph(str(structured.get('summary') or report.content or '暂无内容'), styles['body']))

    key_findings = structured.get('key_findings') or []
    if key_findings:
        story.append(Paragraph('关键发现', styles['heading']))
        for item in key_findings:
            story.append(Paragraph(f'• {item}', styles['body']))

    follow_up_plan = structured.get('follow_up_plan') or []
    if follow_up_plan:
        story.append(Paragraph('建议处理', styles['heading']))
        for item in follow_up_plan:
            story.append(Paragraph(f'• {item}', styles['body']))

    tooth_findings = structured.get('tooth_findings') or []
    if tooth_findings:
        story.append(Paragraph('按牙位问题说明', styles['heading']))
        for tooth in tooth_findings:
            source_label = get_tooth_confidence_label(str(tooth.get('source', 'unknown')))
            story.append(Paragraph(f"{tooth.get('display_name') or tooth.get('tooth_id') or '局部区域'}（{source_label}）", styles['body']))
            for finding in tooth.get('findings', []):
                story.append(
                    Paragraph(
                        f"• {finding.get('finding_label', '待确认病灶')}：{finding.get('clinical_meaning', '')} "
                        f"风险提示：{finding.get('risk_hint', '')} 建议：{finding.get('recommendation', '')}",
                        styles['body'],
                    )
                )
                follow_up_exam = finding.get('follow_up_exam') or []
                if follow_up_exam:
                    story.append(Paragraph('  建议补充检查：' + '、'.join(str(item) for item in follow_up_exam), styles['body']))

    story.append(Paragraph('医生审核意见', styles['heading']))
    story.append(Paragraph(report.doctor_review or structured.get('doctor_notes') or '暂无医生审核意见', styles['body']))

    detection_rows = [['牙位', '问题名称', '严重程度', '置信度', '临床解释']]
    for item in report.image.detections or []:
        detection_rows.append(
            [
                str(item.get('tooth_display_name') or item.get('tooth_id') or '局部区域异常'),
                str(item.get('finding_label') or item.get('class') or '待确认'),
                str(item.get('severity', '待确认')),
                f"{float(item.get('confidence', 0.0)):.0%}",
                str(item.get('clinical_meaning') or item.get('evidence_summary') or '暂无解释'),
            ]
        )

    story.append(Paragraph('检测明细', styles['heading']))
    findings_table = Table(
        detection_rows,
        colWidths=[18 * mm, 28 * mm, 24 * mm, 18 * mm, 84 * mm],
        repeatRows=1,
    )
    findings_table.setStyle(
        TableStyle(
            [
                ('FONTNAME', (0, 0), (-1, -1), 'STSong-Light'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.6),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CFFAFE')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BAE6FD')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(findings_table)

    doc.build(story)
    return buffer.getvalue()
