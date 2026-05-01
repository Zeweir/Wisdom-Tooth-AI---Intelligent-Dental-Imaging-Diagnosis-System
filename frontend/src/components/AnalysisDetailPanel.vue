<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { fetchProtectedBlobUrl } from '../api/http'
import type { AnalysisItem } from '../types/analysis'
import { getImageTypeLabel, getReportStatusLabel } from '../utils/display'

const props = defineProps<{
  currentRecord: AnalysisItem | null
}>()

const previewUrl = ref('')
const previewShellRef = ref<HTMLElement | null>(null)
const imageNaturalSize = ref({ width: 0, height: 0 })
const imageDisplayRect = ref({ left: 0, top: 0, width: 0, height: 0 })
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
  const naturalWidth = imageNaturalSize.value.width
  const naturalHeight = imageNaturalSize.value.height
  const display = imageDisplayRect.value
  if (!naturalWidth || !naturalHeight || !display.width || !display.height) {
    return []
  }
  return detections.map((item, index) => {
    const [x1 = 0, y1 = 0, x2 = 0, y2 = 0] = item.bbox
    const left = display.left + (x1 / naturalWidth) * display.width
    const top = display.top + (y1 / naturalHeight) * display.height
    const width = ((x2 - x1) / naturalWidth) * display.width
    const height = ((y2 - y1) / naturalHeight) * display.height
    return {
      key: `${item.tooth_id}-${item.class}-${index}`,
      label: `${item.tooth_id} ${item.class} ${Math.round(item.confidence * 100)}%`,
      style: {
        left: `${Math.max(0, left)}px`,
        top: `${Math.max(0, top)}px`,
        width: `${Math.max(10, width)}px`,
        height: `${Math.max(10, height)}px`,
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
  imageNaturalSize.value = { width: 0, height: 0 }
  imageDisplayRect.value = { left: 0, top: 0, width: 0, height: 0 }
}

function updateImageDisplayRect() {
  const shell = previewShellRef.value
  if (!shell || !imageNaturalSize.value.width || !imageNaturalSize.value.height) {
    return
  }
  const { clientWidth, clientHeight } = shell
  const naturalRatio = imageNaturalSize.value.width / imageNaturalSize.value.height
  const shellRatio = clientWidth / clientHeight
  let width = clientWidth
  let height = clientHeight
  let left = 0
  let top = 0
  if (shellRatio > naturalRatio) {
    width = clientHeight * naturalRatio
    left = (clientWidth - width) / 2
  } else {
    height = clientWidth / naturalRatio
    top = (clientHeight - height) / 2
  }
  imageDisplayRect.value = { left, top, width, height }
}

function handlePreviewLoad(event: Event) {
  const image = event.target as HTMLImageElement | null
  if (!image?.naturalWidth || !image.naturalHeight) {
    return
  }
  imageNaturalSize.value = {
    width: image.naturalWidth,
    height: image.naturalHeight,
  }
  updateImageDisplayRect()
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
      updateImageDisplayRect()
    } catch {
      previewUrl.value = ''
    }
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('resize', updateImageDisplayRect)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateImageDisplayRect)
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
      <div class="analysis-meta-row">
        <span>患者 {{ currentRecord.patient?.name ?? currentRecord.patient_id }}</span>
        <span v-if="currentRecord.patient?.name">编号 {{ currentRecord.patient_id }}</span>
        <span v-if="currentRecord.patient?.age">年龄 {{ currentRecord.patient.age }}</span>
        <span>{{ currentImageTypeLabel }}</span>
        <span>{{ currentRecord.detections.length }} 个病灶</span>
        <span>平均置信度 {{ averageConfidence }}%</span>
      </div>

      <div class="report-box">
        <div class="sub-title">影像预览</div>
        <div ref="previewShellRef" class="image-preview-shell">
          <img
            v-if="previewUrl"
            :src="previewUrl"
            class="image-preview"
            alt="牙科影像预览"
            @load="handlePreviewLoad"
          />
          <el-empty v-else description="当前文件暂不支持浏览器预览，可通过接口直接下载查看" />
          <div v-if="previewUrl && detectionOverlayBoxes.length > 0" class="bbox-layer" aria-label="AI 检测框叠加层">
            <div v-for="box in detectionOverlayBoxes" :key="box.key" class="bbox-box" :style="box.style">
              <span>{{ box.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="report-box">
        <div class="panel-header">
          <span>重点病灶</span>
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

      <div class="sub-title table-title">检测明细</div>
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
