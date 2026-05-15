<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

import DiagnosisResultCard from '../components/DiagnosisResultCard.vue'
import PageHeader from '../components/PageHeader.vue'
import RecordListPanel from '../components/RecordListPanel.vue'
import ReportReviewPanel from '../components/ReportReviewPanel.vue'
import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import { useWorkbenchContext } from '../workbench'

const route = useRoute()
const workbench = useWorkbenchContext()

const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const hasWorkbenchAccess = workbench.hasWorkbenchAccess
const beginSignOut = workbench.beginSignOut
const canReadImages = workbench.canReadImages
const canReview = workbench.canReview
const canFinalize = workbench.canFinalize
const filters = workbench.filters
const recordsPagination = workbench.recordsPagination
const records = workbench.records
const selectedImageId = workbench.selectedImageId
const currentRecord = workbench.currentRecord
const reviewText = workbench.reviewText
const fetchRecords = workbench.fetchRecords
const applyFilters = workbench.applyFilters
const resetFilters = workbench.resetFilters
const handleRecordsPageChange = workbench.handleRecordsPageChange
const handleRecordsPageSizeChange = workbench.handleRecordsPageSizeChange
const fetchAnalysisRecord = workbench.fetchAnalysisRecord
const handleReviewSubmit = workbench.handleReviewSubmit
const handleFinalizeSubmit = workbench.handleFinalizeSubmit

function getRouteImageId() {
  const value = route.query.image_id
  return Array.isArray(value) ? value[0] : value
}

async function openLinkedCase() {
  const imageId = getRouteImageId()
  if (!imageId || !canReadImages.value) {
    return
  }
  await fetchAnalysisRecord(imageId)
}

watch(
  () => route.query.image_id,
  async () => {
    await openLinkedCase()
  },
)

watch(canReadImages, async (value) => {
  if (value) {
    await openLinkedCase()
  }
})

onMounted(async () => {
  if (canReadImages.value) {
    await fetchRecords()
  }
  await openLinkedCase()
})
</script>

<template>
  <div class="page-stack">
    <PageHeader
      title="AI 诊断"
      description="选择病例后查看影像预览、诊断结论、风险等级与建议处理方案。"
    />

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !hasWorkbenchAccess"
      title="当前账号暂无 AI 诊断访问权限"
      description="请联系管理员为您分配相应角色后再重试。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <section v-else class="diagnosis-page-grid">
      <div>
        <RecordListPanel
          v-if="canReadImages"
          :filters="filters"
          :records="records"
          :pagination="recordsPagination"
          :selected-image-id="selectedImageId"
          @refresh="fetchRecords"
          @apply-filters="applyFilters"
          @reset-filters="resetFilters"
          @page-change="handleRecordsPageChange"
          @page-size-change="handleRecordsPageSizeChange"
          @select="fetchAnalysisRecord"
        />
        <UnauthorizedPanel
          v-else
          title="当前角色不可查看分析记录"
          description="查看影像与诊断结果需要 `read:images` 权限。"
        />
      </div>

      <div class="diagnosis-page-main">
        <DiagnosisResultCard :current-record="currentRecord" />
        <ReportReviewPanel
          v-if="canReview || canReadImages"
          v-model:review-text="reviewText"
          :current-record="currentRecord"
          :can-review="canReview"
          :can-finalize-report="canFinalize"
          @submit="handleReviewSubmit"
          @finalize="handleFinalizeSubmit"
        />
      </div>
    </section>
  </div>
</template>
