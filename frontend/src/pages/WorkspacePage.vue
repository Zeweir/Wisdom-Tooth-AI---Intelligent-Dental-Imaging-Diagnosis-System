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
const clinicalInsights = workbench.clinicalInsights
</script>

<template>
  <div class="page-stack">
    <section class="medical-page-header">
      <div>
        <div class="overview-pill">影像工作站</div>
        <h2>病例接入、分析浏览与报告审核</h2>
        <p>面向医生的核心工作区，只保留病例、影像、诊断意见和审核操作。</p>
      </div>
      <div class="section-heading-tags">
        <el-tag type="info">病例优先</el-tag>
        <el-tag type="success">审核优先</el-tag>
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
      <section class="command-strip">
        <div v-for="item in clinicalInsights" :key="item.label" class="command-strip-item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}{{ item.label === '平均置信度' ? '%' : '' }}</strong>
          <small>{{ item.description }}</small>
        </div>
      </section>

      <section class="section-block">
        <div class="section-heading">
          <div>
            <h3>影像接入与病例列表</h3>
            <p>上传新病例并从右侧快速筛选、定位分析记录。</p>
          </div>
          <el-button v-if="canReadImages" text @click="fetchRecords">刷新列表</el-button>
        </div>

        <div class="grid-layout">
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
      </section>

      <section class="section-block">
        <div class="section-heading">
          <div>
            <h3>影像详情与报告中心</h3>
            <p>围绕当前病例查看 AI 结果，并由医生补充审核意见或正式确认。</p>
          </div>
          <div class="section-heading-tags">
            <el-tag v-if="currentRecord" type="info">患者：{{ currentRecord.patient_id }}</el-tag>
            <el-tag v-if="currentRecord" type="success">{{ getReportStatusLabel(currentRecord.report.status) }}</el-tag>
          </div>
        </div>

        <div class="grid-layout detail-layout">
          <AnalysisDetailPanel v-if="canReadImages" :current-record="currentRecord" />

          <UnauthorizedPanel
            v-else
            title="当前角色不可查看影像详情"
            description="如需浏览检测结果和影像预览，请为用户分配 `read:images` 权限。"
          />

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
