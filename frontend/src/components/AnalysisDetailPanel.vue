<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import { fetchProtectedBlobUrl } from '../api/http'
import type { AnalysisItem } from '../types/analysis'

const props = defineProps<{
  currentRecord: AnalysisItem | null
}>()

const previewUrl = ref('')

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
        <span v-if="currentRecord">{{ currentRecord.image_id }}</span>
      </div>
    </template>

    <el-empty v-if="!currentRecord" description="请选择一条分析记录" />
    <template v-else>
      <div class="summary-row">
        <el-statistic title="病灶数" :value="currentRecord.detections.length" />
        <el-statistic title="当前状态" :value="currentRecord.report.status" />
        <el-statistic title="影像类型" :value="currentRecord.image_type" />
      </div>

      <div class="report-box">
        <div class="sub-title">影像预览</div>
        <el-image
          :src="previewUrl"
          fit="contain"
          style="width: 100%; min-height: 240px; border-radius: 12px; background: #f5f7fa"
          :preview-src-list="previewUrl ? [previewUrl] : []"
        >
          <template #error>
            <el-empty description="当前文件暂不支持浏览器预览，可通过接口直接下载查看" />
          </template>
        </el-image>
      </div>

      <el-table :data="currentRecord.detections" stripe>
        <el-table-column prop="tooth_id" label="牙位" min-width="80" />
        <el-table-column prop="class" label="类别" min-width="120" />
        <el-table-column prop="severity" label="严重程度" min-width="120" />
        <el-table-column label="置信度" min-width="100">
          <template #default="scope">
            {{ (scope.row.confidence * 100).toFixed(0) }}%
          </template>
        </el-table-column>
        <el-table-column label="BBox" min-width="180">
          <template #default="scope">
            {{ scope.row.bbox.join(', ') }}
          </template>
        </el-table-column>
      </el-table>
    </template>
  </el-card>
</template>
