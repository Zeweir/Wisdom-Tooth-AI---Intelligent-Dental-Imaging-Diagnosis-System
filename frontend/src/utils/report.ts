import type { AnalysisItem } from '../types/analysis'
import { getImageTypeLabel, getReportStatusLabel } from './display'

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

export function buildClinicalReportHtml(record: AnalysisItem, reviewOverride?: string) {
  const detections = record.detections
    .map(
      (item) =>
        `<tr><td>${escapeHtml(item.tooth_id)}</td><td>${escapeHtml(item.class)}</td><td>${escapeHtml(item.severity)}</td><td>${Math.round(item.confidence * 100)}%</td></tr>`
    )
    .join('')
  const patientName = record.patient?.name ?? record.patient_id
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>智齿 AI 诊断报告 - ${escapeHtml(record.patient_id)}</title>
  <style>
    body { font-family: "Noto Sans SC", "Plus Jakarta Sans", sans-serif; color: #083344; margin: 40px; line-height: 1.7; background: #f8fafc; }
    main { max-width: 920px; margin: 0 auto; background: #fff; border: 1px solid #bae6fd; border-radius: 18px; padding: 32px; }
    h1 { color: #0e7490; margin: 0 0 8px; }
    h2 { color: #164e63; margin-top: 26px; }
    .meta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 18px; }
    .meta div { border: 1px solid #cffafe; border-radius: 12px; background: #ecfeff; padding: 10px 12px; }
    table { width: 100%; border-collapse: collapse; margin: 18px 0; }
    th, td { border: 1px solid #bae6fd; padding: 10px; text-align: left; }
    th { background: #ecfeff; color: #164e63; }
    p { white-space: pre-wrap; }
    @media print { body { background: #fff; } main { border: 0; padding: 0; } }
  </style>
</head>
<body>
  <main>
    <h1>智齿 AI 口腔影像辅助诊断报告</h1>
    <div>医生确认后方可作为正式诊断报告。</div>
    <section class="meta">
      <div><strong>患者：</strong>${escapeHtml(patientName)}（${escapeHtml(record.patient_id)}）</div>
      <div><strong>影像类型：</strong>${escapeHtml(getImageTypeLabel(record.image_type))}</div>
      <div><strong>影像文件：</strong>${escapeHtml(record.filename)}</div>
      <div><strong>报告状态：</strong>${escapeHtml(getReportStatusLabel(record.report.status))}</div>
    </section>
    <h2>AI 初步诊断意见</h2>
    <p>${escapeHtml(record.report.content || '暂无')}</p>
    <h2>医生审核意见</h2>
    <p>${escapeHtml(reviewOverride || record.report.doctor_review || '暂无')}</p>
    <h2>检测明细</h2>
    <table>
      <thead><tr><th>牙位</th><th>类别</th><th>严重程度</th><th>置信度</th></tr></thead>
      <tbody>${detections || '<tr><td colspan="4">未见明显异常</td></tr>'}</tbody>
    </table>
  </main>
</body>
</html>`
}

export function downloadClinicalReport(record: AnalysisItem, reviewOverride?: string) {
  const blob = new Blob([buildClinicalReportHtml(record, reviewOverride)], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `wisdom-tooth-report-${record.patient_id}.html`
  link.click()
  URL.revokeObjectURL(url)
}

export function printClinicalReport(record: AnalysisItem, reviewOverride?: string) {
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    return
  }
  printWindow.document.write(buildClinicalReportHtml(record, reviewOverride))
  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
}
