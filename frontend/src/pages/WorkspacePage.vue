<script setup lang="ts">
import AnalysisDetailPanel from '../components/AnalysisDetailPanel.vue'
import RecordListPanel from '../components/RecordListPanel.vue'
import ReportReviewPanel from '../components/ReportReviewPanel.vue'
import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import UploadPanel from '../components/UploadPanel.vue'
import { getReportStatusLabel } from '../utils/display'
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()
const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const hasWorkbenchAccess = workbench.hasWorkbenchAccess
const beginSignOut = workbench.beginSignOut
const canReadImages = workbench.canReadImages
const canUpload = workbench.canUpload
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
</script>

<template>
  <div class="page-stack">
    <section class="medical-page-header compact-page-header">
      <div>
        <div class="overview-pill">影像工作站</div>
        <h2>病例队列 → AI 判读 → 报告审核</h2>
        <p>按顺序完成当前病例，不需要在多个页面之间来回切换。</p>
      </div>
    </section>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !hasWorkbenchAccess"
      title="当前账号暂无影像工作站访问权限"
      description="请在 Logto 中为该用户分配 radiologist、doctor 或 chief_doctor 等角色后再重试。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <template v-else>
      <section class="clinical-workbench-grid">
        <div class="workbench-column case-column">
          <div class="step-heading"><span>1</span><strong>选择病例</strong><el-button v-if="canReadImages" text @click="fetchRecords">刷新</el-button></div>
          <UploadPanel
            v-if="canUpload"
            v-model:loading="loading"
            v-model:socket-events="socketEvents"
            :can-upload="canUpload"
            @submit="handleUpload"
          />

          <UnauthorizedPanel
            v-else
            title="当前角色不可上传影像"
            description="上传影像需要 `upload:images` 权限，请为当前用户分配 radiologist 或包含该权限的角色。"
          />

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
            description="查看影像、详情和预览需要 `read:images` 权限。"
          />
        </div>

        <div class="workbench-column image-column">
          <div class="step-heading">
            <span>2</span><strong>查看 AI 判读</strong>
            <div class="section-heading-tags">
              <el-tag v-if="currentRecord" type="info">{{ currentRecord.patient?.name ?? currentRecord.patient_id }}</el-tag>
              <el-tag v-if="currentRecord" type="success">{{ getReportStatusLabel(currentRecord.report.status) }}</el-tag>
            </div>
          </div>
          <AnalysisDetailPanel v-if="canReadImages" :current-record="currentRecord" />
          <UnauthorizedPanel
            v-else
            title="当前角色不可查看影像详情"
            description="如需浏览检测结果和影像预览，请为用户分配 `read:images` 权限。"
          />
        </div>

        <div class="workbench-column report-column">
          <div class="step-heading"><span>3</span><strong>审核报告</strong></div>
          <ReportReviewPanel
            v-if="canReview || canReadImages"
            v-model:review-text="reviewText"
            :current-record="currentRecord"
            :can-review="canReview"
            :can-finalize-report="canFinalize"
            @submit="handleReviewSubmit"
            @finalize="handleFinalizeSubmit"
          />

          <UnauthorizedPanel
            v-else
            title="当前角色不可审核报告"
            description="提交审核意见需要 `review:reports` 权限，正式确认还需要 `finalize:reports` 权限。"
          />
        </div>
      </section>
    </template>
  </div>
</template>
