<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import { fetchProtectedBlobUrl } from '../api/http'
import type { AnalysisItem } from '../types/analysis'
import { getImageTypeLabel, getReportStatusLabel } from '../utils/display'

const props = defineProps<{
  currentRecord: AnalysisItem | null
}>()

const previewUrl = ref('')
const currentStatusLabel = computed(() => (props.currentRecord ? getReportStatusLabel(props.currentRecord.report.status) : ''))
const currentImageTypeLabel = computed(() => (props.currentRecord ? getImageTypeLabel(props.currentRecord.image_type) : ''))
const averageConfidence = computed(() => {
  const detections = props.currentRecord?.detections ?? []
  if (detections.length === 0) {
    return 0
  }
  return Math.round((detections.reduce((sum, item) => sum + item.confidence, 0) / detections.length) * 100)
})
const highConfidenceCount = computed(() => (props.currentRecord?.detections ?? []).filter((item) => item.confidence >= 0.85).length)
const detectionOverlayBoxes = computed(() => {
  const detections = props.currentRecord?.detections ?? []
  const maxX = Math.max(...detections.flatMap((item) => [item.bbox[0] ?? 0, item.bbox[2] ?? 0]), 1)
  const maxY = Math.max(...detections.flatMap((item) => [item.bbox[1] ?? 0, item.bbox[3] ?? 0]), 1)
  return detections.map((item, index) => {
    const [x1 = 0, y1 = 0, x2 = 0, y2 = 0] = item.bbox
    return {
      key: `${item.tooth_id}-${item.class}-${index}`,
      label: `${item.tooth_id} ${item.class} ${Math.round(item.confidence * 100)}%`,
      style: {
        left: `${Math.max(0, Math.min(100, (x1 / maxX) * 100))}%`,
        top: `${Math.max(0, Math.min(100, (y1 / maxY) * 100))}%`,
        width: `${Math.max(8, Math.min(100, ((x2 - x1) / maxX) * 100))}%`,
        height: `${Math.max(8, Math.min(100, ((y2 - y1) / maxY) * 100))}%`,
      }
    }
  })
})
const riskItems = computed(() => {
  return (props.currentRecord?.detections ?? []).slice(0, 4).map((item) => ({
    key: `${item.tooth_id}-${item.class}-${item.severity}`,
    title: `${item.tooth_id} ${item.class}`,
    description: `${item.severity} / 置信度 ${Math.round(item.confidence * 100)}%`,
    percentage: Math.round(item.confidence * 100)
  }))
})

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
    } catch {
      previewUrl.value = ''
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  resetPreviewUrl()
})
</script>

<template>
  <el-card class="panel" shadow="never">
    <template #header>
      <div class="panel-header">
        <span>AI 检测结果</span>
        <el-tag v-if="currentRecord" type="info">{{ currentImageTypeLabel }}</el-tag>
      </div>
    </template>

    <el-empty v-if="!currentRecord" description="请选择一条分析记录" />
    <template v-else>
      <div class="summary-row">
        <el-statistic title="病灶数" :value="currentRecord.detections.length" />
        <el-statistic title="当前状态" :value="currentStatusLabel" />
        <el-statistic title="影像类型" :value="currentImageTypeLabel" />
        <el-statistic title="平均置信度" :value="`${averageConfidence}%`" />
      </div>

      <div class="diagnosis-steps">
        <div class="diagnosis-step">
          <strong>影像读取</strong>
          <span>已完成文件载入和病例绑定</span>
        </div>
        <div class="diagnosis-step">
          <strong>AI 判读</strong>
          <span>{{ currentRecord.detections.length > 0 ? '已生成结构化检测结果' : '暂无检测结果' }}</span>
        </div>
        <div class="diagnosis-step">
          <strong>医生确认</strong>
          <span>{{ currentStatusLabel }}</span>
        </div>
      </div>

      <div class="report-box">
        <div class="sub-title">病例摘要</div>
        <div class="overview-list">
          <div class="overview-list-item">
            <strong>患者编号</strong>
            <span>{{ currentRecord.patient_id }}</span>
          </div>
          <div class="overview-list-item">
            <strong>影像文件</strong>
            <span>{{ currentRecord.filename }}</span>
          </div>
          <div class="overview-list-item">
            <strong>报告状态</strong>
            <span>{{ currentStatusLabel }}</span>
          </div>
        </div>
      </div>

      <div class="report-box">
        <div class="sub-title">影像预览</div>
        <div class="image-preview-shell">
          <el-image
            :src="previewUrl"
            fit="contain"
            class="image-preview"
            :preview-src-list="previewUrl ? [previewUrl] : []"
          >
            <template #error>
              <el-empty description="当前文件暂不支持浏览器预览，可通过接口直接下载查看" />
            </template>
          </el-image>
          <div v-if="previewUrl && detectionOverlayBoxes.length > 0" class="bbox-layer" aria-label="AI 检测框叠加层">
            <div v-for="box in detectionOverlayBoxes" :key="box.key" class="bbox-box" :style="box.style">
              <span>{{ box.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="report-box">
        <div class="panel-header">
          <span>病灶风险概览</span>
          <el-tag type="success">高置信 {{ highConfidenceCount }} 项</el-tag>
        </div>
        <el-empty v-if="riskItems.length === 0" description="暂无病灶风险项" />
        <div v-else class="risk-list">
          <div v-for="item in riskItems" :key="item.key" class="risk-item">
            <div class="risk-meta">
              <strong>{{ item.title }}</strong>
              <span>{{ item.description }}</span>
            </div>
            <el-progress :percentage="item.percentage" :stroke-width="8" style="min-width: 130px" />
          </div>
        </div>
      </div>

      <el-table :data="currentRecord.detections" stripe>
        <el-table-column prop="tooth_id" label="牙位" min-width="80" />
        <el-table-column prop="class" label="类别" min-width="120" />
        <el-table-column prop="severity" label="严重程度" min-width="120" />
        <el-table-column label="置信度" min-width="100">
          <template #default="scope">
            <div class="confidence-cell">
              <span>{{ (scope.row.confidence * 100).toFixed(0) }}%</span>
              <el-progress :percentage="Math.round(scope.row.confidence * 100)" :show-text="false" :stroke-width="6" />
            </div>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </el-card>
</template>
