<script setup lang="ts">
import type { AnalysisItem } from '../types/analysis'

const props = defineProps<{
  record: AnalysisItem | null
}>()

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function buildReportHtml(record: AnalysisItem) {
  const detections = record.detections
    .map((item) => `<tr><td>${escapeHtml(item.tooth_id)}</td><td>${escapeHtml(item.class)}</td><td>${escapeHtml(item.severity)}</td><td>${Math.round(item.confidence * 100)}%</td></tr>`)
    .join('')
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>智齿 AI 诊断报告 - ${escapeHtml(record.patient_id)}</title>
  <style>
    body { font-family: "Noto Sans SC", sans-serif; color: #0f172a; margin: 32px; line-height: 1.7; }
    h1 { color: #2563eb; }
    table { width: 100%; border-collapse: collapse; margin: 16px 0; }
    th, td { border: 1px solid #dbe3ef; padding: 8px; text-align: left; }
    th { background: #f8fafc; }
  </style>
</head>
<body>
  <h1>智齿 AI 牙齿影像智能诊断报告</h1>
  <p><strong>患者：</strong>${escapeHtml(record.patient?.name ?? record.patient_id)}（${escapeHtml(record.patient_id)}）</p>
  <p><strong>影像文件：</strong>${escapeHtml(record.filename)}</p>
  <p><strong>影像类型：</strong>${escapeHtml(record.image_type)}</p>
  <h2>AI 诊断内容</h2>
  <p>${escapeHtml(record.report.content || '暂无')}</p>
  <h2>医生审核意见</h2>
  <p>${escapeHtml(record.report.doctor_review || '暂无')}</p>
  <h2>检测明细</h2>
  <table>
    <thead><tr><th>牙位</th><th>类别</th><th>严重程度</th><th>置信度</th></tr></thead>
    <tbody>${detections}</tbody>
  </table>
</body>
</html>`
}

function downloadReport(record: AnalysisItem) {
  const html = buildReportHtml(record)
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `wisdom-tooth-report-${record.patient_id}.html`
  link.click()
  URL.revokeObjectURL(url)
}

function printReport(record: AnalysisItem) {
  const html = buildReportHtml(record)
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    return
  }
  printWindow.document.write(html)
  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
}
</script>

<template>
  <el-empty v-if="!props.record" description="请选择一条报告记录" />
  <div v-else class="report-preview">
    <div class="report-preview-meta">
      <span>患者：{{ props.record.patient?.name ?? props.record.patient_id }}</span>
      <span>影像：{{ props.record.filename }}</span>
      <span>诊断时间：{{ new Date(props.record.updated_at).toLocaleString() }}</span>
    </div>
    <article class="report-box">
      <div class="sub-title">AI 诊断内容</div>
      <p class="clinical-copy">{{ props.record.report.content || '暂无 AI 诊断内容' }}</p>
    </article>
    <article class="report-box">
      <div class="sub-title">医生审核意见</div>
      <p class="clinical-copy">{{ props.record.report.doctor_review || '暂无医生审核意见' }}</p>
    </article>
    <div class="report-preview-actions">
      <el-button type="primary" @click="downloadReport(props.record)">下载报告</el-button>
      <el-button @click="printReport(props.record)">打印预览</el-button>
    </div>
  </div>
</template>
