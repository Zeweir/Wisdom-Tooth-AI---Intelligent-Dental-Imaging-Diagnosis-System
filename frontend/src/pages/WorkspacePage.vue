<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DiagnosisResultCard from '../components/DiagnosisResultCard.vue'
import PageHeader from '../components/PageHeader.vue'
import RecordListPanel from '../components/RecordListPanel.vue'
import ReportReviewPanel from '../components/ReportReviewPanel.vue'
import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import UploadPanel from '../components/UploadPanel.vue'
import { useWorkbenchContext } from '../workbench'

const route = useRoute()
const router = useRouter()
const workbench = useWorkbenchContext()

const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const hasWorkbenchAccess = workbench.hasWorkbenchAccess
const beginSignOut = workbench.beginSignOut
const canUpload = workbench.canUpload
const canReadImages = workbench.canReadImages
const canReview = workbench.canReview
const canFinalize = workbench.canFinalize
const loading = workbench.loading
const socketEvents = workbench.socketEvents
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
const handleUpload = workbench.handleUpload
const handleReviewSubmit = workbench.handleReviewSubmit
const handleFinalizeSubmit = workbench.handleFinalizeSubmit
const activePane = ref<'upload' | 'records' | 'diagnosis' | 'report'>('upload')

const workflowStats = computed(() => {
  const pendingReview = records.value.filter((record) => record.report.status === 'ai_generated').length
  const finalized = records.value.filter((record) => record.report.status === 'finalized').length
  const processing = records.value.filter((record) => record.status === 'processing').length
  return [
    { label: '待审核', value: pendingReview },
    { label: '处理中', value: processing },
    { label: '已归档', value: finalized },
  ]
})
const currentCaseStatus = computed(() => {
  if (!currentRecord.value) {
    return {
      title: '尚未选择病例',
      description: '上传影像或从病例队列选择记录后，可在右侧完成诊断复核与报告审核。',
      tag: '待开始',
      type: 'info' as const,
    }
  }
  if (currentRecord.value.status === 'processing') {
    return {
      title: 'AI 正在分析影像',
      description: '分析完成后会刷新检测结果、风险等级和报告草稿。',
      tag: '分析中',
      type: 'warning' as const,
    }
  }
  if (currentRecord.value.report.status === 'finalized') {
    return {
      title: '病例已归档',
      description: '该病例已形成正式报告，可继续打印、导出或查看版本历史。',
      tag: '已归档',
      type: 'success' as const,
    }
  }
  return {
    title: '等待医生复核',
    description: '请确认检测框、AI 结论和医生意见后保存审核。',
    tag: '待复核',
    type: 'primary' as const,
  }
})

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

function selectRecord(imageId: string) {
  void fetchAnalysisRecord(imageId)
  void router.replace({ path: '/workspace', query: { ...route.query, image_id: imageId } })
  activePane.value = 'diagnosis'
}

watch(
  () => route.query.image_id,
  async () => {
    await openLinkedCase()
  },
)

watch(canReadImages, async (value) => {
  if (value) {
    await fetchRecords()
    await openLinkedCase()
  }
})

watch(selectedImageId, (imageId) => {
  if (!imageId || route.path !== '/workspace' || getRouteImageId() === imageId) {
    return
  }
  void router.replace({ path: '/workspace', query: { ...route.query, image_id: imageId } })
})

watch(currentRecord, (record) => {
  if (record && activePane.value === 'upload') {
    activePane.value = 'diagnosis'
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
  <div class="page-stack workspace-page">
    <PageHeader
      title="影像工作站"
      description="从影像上传、AI 诊断、病例队列到报告审核，集中在一个临床工作流中完成。"
    >
      <template #actions>
        <div class="workspace-header-stats">
          <span v-for="item in workflowStats" :key="item.label">{{ item.label }} {{ item.value }}</span>
        </div>
      </template>
    </PageHeader>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !hasWorkbenchAccess"
      title="当前账号暂无影像工作站访问权限"
      description="请联系管理员为您分配相应角色后再重试。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <template v-else>
      <nav class="workspace-mobile-switch" aria-label="影像工作站流程">
        <button type="button" :class="{ active: activePane === 'upload' }" @click="activePane = 'upload'">上传</button>
        <button type="button" :class="{ active: activePane === 'records' }" @click="activePane = 'records'">病例</button>
        <button type="button" :class="{ active: activePane === 'diagnosis' }" @click="activePane = 'diagnosis'">诊断</button>
        <button type="button" :class="{ active: activePane === 'report' }" @click="activePane = 'report'">报告</button>
      </nav>

      <section class="workspace-case-status">
        <div>
          <strong>{{ currentCaseStatus.title }}</strong>
          <p>{{ currentCaseStatus.description }}</p>
        </div>
        <el-tag :type="currentCaseStatus.type">{{ currentCaseStatus.tag }}</el-tag>
      </section>

      <section class="workspace-shell">
      <aside class="workspace-rail">
        <div class="workspace-pane workspace-upload-pane" :class="{ active: activePane === 'upload' }">
          <UploadPanel
            v-model:loading="loading"
            v-model:socket-events="socketEvents"
            :can-upload="canUpload"
            @submit="handleUpload"
          />
        </div>

        <div class="workspace-pane workspace-records-pane" :class="{ active: activePane === 'records' }">
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
            @select="selectRecord"
          />
          <UnauthorizedPanel
            v-else
            title="当前角色不可查看分析记录"
            description="查看影像与诊断结果需要 `read:images` 权限。"
          />
        </div>
      </aside>

      <main class="workspace-review">
        <div v-if="!currentRecord" class="empty-action-card workspace-empty-case">
          <strong>请选择或上传病例</strong>
          <p>工作站会把影像预览、检测框、诊断结论和报告审核放在同一条流程里。</p>
          <div class="quick-action-row">
            <el-button type="primary" @click="activePane = 'upload'">上传影像</el-button>
            <el-button @click="activePane = 'records'">查看病例队列</el-button>
          </div>
        </div>
        <template v-else>
          <div class="workspace-pane workspace-diagnosis-pane" :class="{ active: activePane === 'diagnosis' }">
            <DiagnosisResultCard :current-record="currentRecord" />
          </div>
          <div class="workspace-pane workspace-report-pane" :class="{ active: activePane === 'report' }">
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
        </template>
      </main>
      </section>
    </template>
  </div>
</template>
