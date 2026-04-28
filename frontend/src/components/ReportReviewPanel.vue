<script setup lang="ts">
import { computed } from 'vue'
import type { AnalysisItem } from '../types/analysis'
import { getReportStatusLabel, getReportStatusTagType } from '../utils/display'

const props = defineProps<{
  currentRecord: AnalysisItem | null
  canReview: boolean
  canFinalizeReport: boolean
}>()

const reviewText = defineModel<string>('reviewText', { required: true })
const canSubmit = computed(() => Boolean(props.currentRecord) && props.canReview)
const canFinalize = computed(() => props.currentRecord?.report.status === 'doctor_reviewed' && props.canFinalizeReport)
const currentStatusLabel = computed(() => (props.currentRecord ? getReportStatusLabel(props.currentRecord.report.status) : ''))
const currentStatusTagType = computed(() => (props.currentRecord ? getReportStatusTagType(props.currentRecord.report.status) : 'info'))
const reviewTextLength = computed(() => reviewText.value.trim().length)
const reportTextLength = computed(() => props.currentRecord?.report.content.length ?? 0)

const emit = defineEmits<{
  submit: []
  finalize: []
}>()

function buildReportHtml() {
  if (!props.currentRecord) {
    return ''
  }
  const escapeHtml = (value: string) =>
    value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  const detections = props.currentRecord.detections
    .map(
      (item) =>
        `<tr><td>${escapeHtml(item.tooth_id)}</td><td>${escapeHtml(item.class)}</td><td>${escapeHtml(item.severity)}</td><td>${Math.round(item.confidence * 100)}%</td></tr>`
    )
    .join('')
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>智齿 AI 诊断报告 - ${escapeHtml(props.currentRecord.patient_id)}</title>
  <style>
    body { font-family: "Noto Sans SC", sans-serif; color: #083344; margin: 40px; line-height: 1.7; }
    h1 { color: #0e7490; }
    table { width: 100%; border-collapse: collapse; margin: 18px 0; }
    th, td { border: 1px solid #bae6fd; padding: 10px; text-align: left; }
    th { background: #ecfeff; }
    .section { margin-top: 24px; }
  </style>
</head>
<body>
  <h1>智齿 AI 口腔影像辅助诊断报告</h1>
  <p><strong>患者编号：</strong>${escapeHtml(props.currentRecord.patient_id)}</p>
  <p><strong>影像文件：</strong>${escapeHtml(props.currentRecord.filename)}</p>
  <p><strong>报告状态：</strong>${escapeHtml(currentStatusLabel.value)}</p>
  <div class="section">
    <h2>AI 初步诊断意见</h2>
    <p>${escapeHtml(props.currentRecord.report.content)}</p>
  </div>
  <div class="section">
    <h2>检测结果</h2>
    <table><thead><tr><th>牙位</th><th>类别</th><th>严重程度</th><th>置信度</th></tr></thead><tbody>${detections}</tbody></table>
  </div>
  <div class="section">
    <h2>医生审核意见</h2>
    <p>${escapeHtml(reviewText.value || props.currentRecord.report.doctor_review || '暂无')}</p>
  </div>
</body>
</html>`
}

function handlePrintReport() {
  const html = buildReportHtml()
  if (!html) {
    return
  }
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    return
  }
  printWindow.document.write(html)
  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
}

function handleExportHtml() {
  if (!props.currentRecord) {
    return
  }
  const html = buildReportHtml()
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `wisdom-tooth-report-${props.currentRecord.patient_id}.html`
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <el-card class="panel" shadow="never">
    <template #header>
      <div class="panel-header">
        <span>报告审核</span>
        <el-tag type="warning">医生确认后方可作为正式报告</el-tag>
      </div>
    </template>

    <el-empty v-if="!currentRecord" description="请选择一条分析记录" />
    <template v-else>
      <div class="report-box">
        <div class="panel-header">
          <span>AI 初步诊断意见</span>
          <el-tag type="info">{{ reportTextLength }} 字</el-tag>
        </div>
        <p>{{ currentRecord.report.content }}</p>
      </div>
      <div class="report-box">
        <div class="panel-header">
          <span>诊断报告流程</span>
          <el-tag :type="currentStatusTagType">{{ currentStatusLabel }}</el-tag>
        </div>
        <div class="diagnosis-steps">
          <div class="diagnosis-step">
            <strong>AI 生成</strong>
            <span>结构化结果转诊断初稿</span>
          </div>
          <div class="diagnosis-step">
            <strong>医生审核</strong>
            <span>{{ currentRecord.report.doctor_review ? '已填写审核意见' : '等待医生补充' }}</span>
          </div>
          <div class="diagnosis-step">
            <strong>正式确认</strong>
            <span>{{ currentRecord.report.status === 'finalized' ? '已完成' : '需主任医生确认' }}</span>
          </div>
        </div>
      </div>
      <div class="report-box">
        <div class="panel-header">
          <span>医生补充意见</span>
          <el-tag type="success">{{ reviewTextLength }} 字</el-tag>
        </div>
        <el-input
          v-model="reviewText"
          type="textarea"
          :rows="6"
          placeholder="例如：AI诊断基本准确，建议补充根尖片确认根尖状态"
        />
      </div>
      <div class="actions">
        <el-button type="primary" :disabled="!canSubmit" @click="emit('submit')">保存审核意见</el-button>
        <el-button type="success" :disabled="!canFinalize" @click="emit('finalize')">确认为正式报告</el-button>
        <el-button :disabled="!currentRecord" @click="handlePrintReport">打印预览</el-button>
        <el-button :disabled="!currentRecord" @click="handleExportHtml">导出 HTML</el-button>
      </div>
    </template>
  </el-card>
</template>
