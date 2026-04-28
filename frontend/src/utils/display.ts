import type { AnalysisItem, ReportStatus } from '../types/analysis'

const imageTypeLabels: Record<AnalysisItem['image_type'], string> = {
  panoramic: '全景片',
  periapical: '根尖片',
  cbct: 'CBCT'
}

const reportStatusLabels: Record<ReportStatus, string> = {
  processing: '分析中',
  ai_generated: 'AI 已生成',
  doctor_reviewed: '医生已审核',
  finalized: '正式报告'
}

const reportStatusTagTypes: Record<ReportStatus, 'info' | 'warning' | 'success'> = {
  processing: 'info',
  ai_generated: 'warning',
  doctor_reviewed: 'warning',
  finalized: 'success'
}

const scopeLabels: Record<string, string> = {
  'read:images': '查看影像',
  'upload:images': '上传影像',
  'review:reports': '审核报告',
  'finalize:reports': '确认正式报告'
}

export function getImageTypeLabel(imageType: AnalysisItem['image_type']) {
  return imageTypeLabels[imageType] ?? imageType
}

export function getReportStatusLabel(status: ReportStatus) {
  return reportStatusLabels[status] ?? status
}

export function getReportStatusTagType(status: ReportStatus) {
  return reportStatusTagTypes[status] ?? 'info'
}

export function getScopeLabel(scope: string) {
  return scopeLabels[scope] ?? scope
}
