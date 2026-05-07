<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { fetchProtectedBlobUrl } from '../api/http'
import type { AnalysisItem } from '../types/analysis'
import { downloadClinicalReport } from '../utils/report'
import ToothOverviewChart from './ToothOverviewChart.vue'

const props = defineProps<{
  currentRecord: AnalysisItem | null
}>()

const previewUrl = ref('')
const imageRef = ref<HTMLImageElement | null>(null)
const previewShellRef = ref<HTMLElement | null>(null)
const previewSize = ref({ width: 0, height: 0 })
const naturalSize = ref({ width: 0, height: 0 })
const selectedToothKey = ref<string | null>(null)
let resizeObserver: ResizeObserver | null = null

const averageConfidence = computed(() => {
  const detections = props.currentRecord?.detections ?? []
  if (!detections.length) {
    return 0
  }
  return Math.round((detections.reduce((sum, item) => sum + item.confidence, 0) / detections.length) * 100)
})

const riskLevel = computed(() => {
  const severities = (props.currentRecord?.detections ?? []).map((item) => item.severity.toLowerCase())
  if (severities.some((item) => item.includes('重') || item.includes('high'))) {
    return { label: '高风险', type: 'danger' as const }
  }
  if (severities.some((item) => item.includes('中') || item.includes('medium'))) {
    return { label: '中风险', type: 'warning' as const }
  }
  return { label: '低风险', type: 'success' as const }
})

const conclusion = computed(() => {
  return props.currentRecord?.report.structured_content.summary || props.currentRecord?.report.content || '未见明显异常'
})

const recommendation = computed(() => {
  const plans = props.currentRecord?.report.structured_content.follow_up_plan ?? []
  if (!plans.length) {
    return '建议结合患者主诉与体征进行常规随访。'
  }
  return plans.join('；')
})
const toothFindingGroups = computed(() => {
  const reportGroups = props.currentRecord?.report.structured_content.tooth_findings ?? []
  if (reportGroups.length > 0) {
    return reportGroups
  }
  const grouped = new Map<string, { tooth_id: string; display_name: string; source: "model_mapped" | "layout_inferred" | "unknown"; findings: Array<{
    finding_label: string
    severity: string
    confidence: number
    clinical_meaning: string
    risk_hint: string
    recommendation: string
    evidence_summary: string
    follow_up_exam: string[]
  }> }>()
  for (const item of props.currentRecord?.detections ?? []) {
    const displayName = item.tooth_display_name || item.tooth_id || '局部区域异常'
    const group = grouped.get(displayName) ?? {
      tooth_id: item.tooth_id,
      display_name: displayName,
      source: item.tooth_confidence_source || 'unknown',
      findings: [],
    }
    group.findings.push({
      finding_label: item.finding_label || item.class,
      severity: item.severity,
      confidence: item.confidence,
      clinical_meaning: item.clinical_meaning || '',
      risk_hint: item.risk_hint || '',
      recommendation: item.recommendation || '',
      evidence_summary: item.evidence_summary || '',
      follow_up_exam: item.follow_up_exam || [],
    })
    grouped.set(displayName, group)
  }
  return Array.from(grouped.values())
})

const detectionBoxes = computed(() => {
  const record = props.currentRecord
  const naturalWidth = naturalSize.value.width
  const naturalHeight = naturalSize.value.height
  const shellWidth = previewSize.value.width
  const shellHeight = previewSize.value.height

  if (!record || !naturalWidth || !naturalHeight || !shellWidth || !shellHeight) {
    return []
  }

  const scale = Math.min(shellWidth / naturalWidth, shellHeight / naturalHeight)
  const displayWidth = naturalWidth * scale
  const displayHeight = naturalHeight * scale
  const offsetX = (shellWidth - displayWidth) / 2
  const offsetY = (shellHeight - displayHeight) / 2

  return record.detections
    .map((item, index) => {
      const [rawX1 = 0, rawY1 = 0, rawX2 = 0, rawY2 = 0] = item.bbox
      const normalized = [rawX1, rawY1, rawX2, rawY2].every((value) => value >= 0 && value <= 1)
      const x1 = normalized ? rawX1 * naturalWidth : rawX1
      const y1 = normalized ? rawY1 * naturalHeight : rawY1
      const x2 = normalized ? rawX2 * naturalWidth : rawX2
      const y2 = normalized ? rawY2 * naturalHeight : rawY2
      const left = offsetX + Math.max(0, Math.min(x1, x2)) * scale
      const top = offsetY + Math.max(0, Math.min(y1, y2)) * scale
      const width = Math.max(24, Math.abs(x2 - x1) * scale)
      const height = Math.max(24, Math.abs(y2 - y1) * scale)
      const severity = item.severity.toLowerCase()

      return {
        key: `${item.tooth_id}-${item.class}-${index}`,
        toothKey: item.tooth_display_name || item.tooth_id,
        label: `${item.tooth_display_name || item.tooth_id} ${item.finding_label || item.class} ${Math.round(item.confidence * 100)}%`,
        className: {
          'is-selected': selectedToothKey.value === (item.tooth_display_name || item.tooth_id),
          'is-high-risk': severity.includes('重') || severity.includes('high'),
          'is-medium-risk': severity.includes('中') || severity.includes('medium'),
          'is-low-risk': severity.includes('低') || severity.includes('low'),
        },
        style: {
          left: `${left}px`,
          top: `${top}px`,
          width: `${width}px`,
          height: `${height}px`,
        },
      }
    })
    .filter((item) => Number.parseFloat(item.style.width) > 0 && Number.parseFloat(item.style.height) > 0)
})

function updatePreviewSize() {
  if (!previewShellRef.value) {
    previewSize.value = { width: 0, height: 0 }
    return
  }
  const rect = previewShellRef.value.getBoundingClientRect()
  previewSize.value = { width: rect.width, height: rect.height }
}

function handleImageLoad() {
  if (!imageRef.value) {
    naturalSize.value = { width: 0, height: 0 }
    return
  }
  naturalSize.value = {
    width: imageRef.value.naturalWidth,
    height: imageRef.value.naturalHeight,
  }
  updatePreviewSize()
}

function resetPreviewUrl() {
  if (previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = ''
}

watch(
  () => props.currentRecord?.image_url,
  async (imageUrl) => {
    resetPreviewUrl()
    if (!imageUrl) {
      return
    }
    try {
      previewUrl.value = await fetchProtectedBlobUrl(imageUrl)
      await nextTick()
      updatePreviewSize()
    } catch {
      previewUrl.value = ''
    }
  },
  { immediate: true },
)

watch(
  () => props.currentRecord?.image_id,
  () => {
    selectedToothKey.value = null
  }
)

onMounted(() => {
  resizeObserver = new ResizeObserver(updatePreviewSize)
  if (previewShellRef.value) {
    resizeObserver.observe(previewShellRef.value)
  }
  updatePreviewSize()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resetPreviewUrl()
})

function handleDownloadPdf() {
  if (!props.currentRecord) {
    return
  }
  void downloadClinicalReport(props.currentRecord)
}

function getToothSourceLabel(source: string | undefined) {
  if (source === 'model_mapped') {
    return '模型牙位'
  }
  if (source === 'layout_inferred') {
    return '推测牙位'
  }
  return '局部区域'
}

function handleToothSelect(toothKey: string | null) {
  selectedToothKey.value = toothKey
}
</script>

<template>
  <el-card class="panel" shadow="never">
    <template #header>
      <div class="panel-header">
        <span>AI 诊断结果</span>
        <el-tag v-if="currentRecord" :type="riskLevel.type">{{ riskLevel.label }}</el-tag>
      </div>
    </template>

    <el-empty v-if="!currentRecord" description="请选择病例查看诊断结果" />
    <template v-else>
      <el-alert
        v-if="currentRecord.status === 'processing'"
        title="影像正在分析中，结果会自动更新"
        type="info"
        :closable="false"
        show-icon
      />

      <div class="diagnosis-result-layout">
        <div class="diagnosis-preview">
          <div class="diagnosis-preview-title">影像预览</div>
          <div ref="previewShellRef" class="image-preview-shell">
            <img
              v-if="previewUrl"
              ref="imageRef"
              :src="previewUrl"
              class="image-preview"
              alt="牙科影像预览"
              @load="handleImageLoad"
            />
            <div v-if="previewUrl && detectionBoxes.length > 0" class="detection-overlay" aria-hidden="true">
              <div
                v-for="box in detectionBoxes"
                :key="box.key"
                class="detection-box"
                :class="box.className"
                :style="box.style"
              >
                <span class="detection-box-label">{{ box.label }}</span>
              </div>
            </div>
            <el-empty v-if="!previewUrl" description="暂无可预览影像" />
          </div>
        </div>

        <div class="diagnosis-summary">
          <div class="summary-item">
            <span>AI 诊断结论</span>
            <strong>{{ conclusion }}</strong>
          </div>
          <div class="summary-item">
            <span>置信度</span>
            <strong>{{ averageConfidence }}%</strong>
            <el-progress :percentage="averageConfidence" :stroke-width="8" />
          </div>
          <div class="summary-item">
            <span>高优先级问题</span>
            <div class="tag-wrap">
              <el-tag
                v-for="item in currentRecord.report.structured_content.high_priority_findings"
                :key="item"
                type="danger"
                effect="light"
              >
                {{ item }}
              </el-tag>
              <el-tag v-if="currentRecord.report.structured_content.high_priority_findings.length === 0" type="success" effect="light">
                暂无高优先问题
              </el-tag>
            </div>
          </div>
          <div class="summary-item">
            <span>建议处理方案</span>
            <p>{{ recommendation }}</p>
          </div>
          <div class="summary-item">
            <span>正式 PDF 报告</span>
            <div class="quick-action-row">
              <el-button type="primary" @click="handleDownloadPdf">下载 PDF 报告</el-button>
              <el-tag v-if="currentRecord.report.pdf_variant" type="info">{{ currentRecord.report.pdf_variant }}</el-tag>
            </div>
          </div>
        </div>
      </div>

      <div class="diagnosis-findings-grid">
        <ToothOverviewChart
          :tooth-findings="toothFindingGroups"
          :selected-tooth-key="selectedToothKey"
          @select="handleToothSelect"
        />
        <article
          v-for="group in toothFindingGroups"
          :key="`${group.display_name}-${group.source}`"
          class="diagnosis-finding-card diagnosis-tooth-card"
          :class="{ 'is-selected': selectedToothKey === group.display_name }"
          @click="handleToothSelect(selectedToothKey === group.display_name ? null : group.display_name)"
        >
          <div class="panel-header">
            <strong>{{ group.display_name }}</strong>
            <el-tag :type="group.source === 'layout_inferred' ? 'warning' : group.source === 'unknown' ? 'info' : 'success'">
              {{ getToothSourceLabel(group.source) }}
            </el-tag>
          </div>
          <div class="diagnosis-tooth-findings">
            <article
              v-for="item in group.findings"
              :key="`${group.display_name}-${item.finding_label}-${item.confidence}`"
              class="diagnosis-tooth-finding"
            >
              <div class="panel-header">
                <span>{{ item.finding_label }}</span>
                <el-tag :type="item.severity.includes('高') ? 'danger' : item.severity.includes('中') ? 'warning' : 'success'">
                  {{ Math.round(item.confidence * 100) }}%
                </el-tag>
              </div>
              <div class="record-meta">
                <span>{{ item.severity }}</span>
                <span v-if="item.follow_up_exam.length > 0">补充 {{ item.follow_up_exam.join('、') }}</span>
              </div>
              <p class="clinical-copy"><strong>临床含义：</strong>{{ item.clinical_meaning || item.evidence_summary || '暂无解释' }}</p>
              <p class="clinical-copy"><strong>风险提示：</strong>{{ item.risk_hint || '请结合医生复核。' }}</p>
              <p class="clinical-copy"><strong>处理建议：</strong>{{ item.recommendation || '建议结合临床检查确认。' }}</p>
            </article>
          </div>
        </article>
      </div>
    </template>
  </el-card>
</template>
