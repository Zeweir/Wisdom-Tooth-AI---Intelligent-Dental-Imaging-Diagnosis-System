<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

import { fetchProtectedBlobUrl } from '../api/http'
import type { AnalysisItem } from '../types/analysis'

const props = defineProps<{
  currentRecord: AnalysisItem | null
}>()

const previewUrl = ref('')

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
  const count = props.currentRecord?.detections.length ?? 0
  if (count === 0) {
    return '未见明显异常'
  }
  return `检测到 ${count} 项疑似问题，建议结合临床复核`
})

const suspectedProblems = computed(() => {
  const classes = (props.currentRecord?.detections ?? []).map((item) => item.class)
  return Array.from(new Set(classes))
})

const recommendation = computed(() => {
  if ((props.currentRecord?.detections.length ?? 0) === 0) {
    return '建议结合患者主诉与体征进行常规随访。'
  }
  if (riskLevel.value.label === '高风险') {
    return '建议优先安排专科复诊，必要时补充 CBCT 或根尖片。'
  }
  if (riskLevel.value.label === '中风险') {
    return '建议在一周内复查并结合临床检查确认病灶范围。'
  }
  return '建议常规复查并进行口腔卫生管理。'
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
      await nextTick()
    } catch {
      previewUrl.value = ''
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  resetPreviewUrl()
})
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
          <div class="image-preview-shell">
            <img v-if="previewUrl" :src="previewUrl" class="image-preview" alt="牙科影像预览" />
            <el-empty v-else description="暂无可预览影像" />
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
            <span>疑似问题</span>
            <div class="tag-wrap">
              <el-tag v-for="item in suspectedProblems" :key="item" type="warning" effect="light">{{ item }}</el-tag>
              <el-tag v-if="suspectedProblems.length === 0" type="success" effect="light">无明显异常</el-tag>
            </div>
          </div>
          <div class="summary-item">
            <span>建议处理方案</span>
            <p>{{ recommendation }}</p>
          </div>
        </div>
      </div>
    </template>
  </el-card>
</template>
