<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'

import PageHeader from '../components/PageHeader.vue'
import ReportPreview from '../components/ReportPreview.vue'
import StatusTag from '../components/StatusTag.vue'
import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import type { AnalysisItem } from '../types/analysis'
import { getImageTypeLabel } from '../utils/display'
import { downloadClinicalReport } from '../utils/report'
import { useWorkbenchContext } from '../workbench'

const route = useRoute()
const workbench = useWorkbenchContext()

const canReadImages = workbench.canReadImages
const filters = workbench.filters
const recordsPagination = workbench.recordsPagination
const records = workbench.records
const fetchRecords = workbench.fetchRecords
const applyFilters = workbench.applyFilters
const resetFilters = workbench.resetFilters
const handleRecordsPageChange = workbench.handleRecordsPageChange
const handleRecordsPageSizeChange = workbench.handleRecordsPageSizeChange
const fetchAnalysisRecord = workbench.fetchAnalysisRecord
const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const beginSignOut = workbench.beginSignOut

const detailVisible = ref(false)
const selectedRecord = ref<AnalysisItem | null>(null)

const recordsWithIndex = computed(() => {
  return records.value.map((item, index) => ({
    ...item,
    rowNo: recordsPagination.value.offset + index + 1,
  }))
})

function openDetail(record: AnalysisItem) {
  selectedRecord.value = record
  detailVisible.value = true
}

function generateReport(record: AnalysisItem) {
  selectedRecord.value = record
  detailVisible.value = true
  ElMessage.success('报告内容已生成，可在详情中下载或打印')
}

function getResultText(record: AnalysisItem) {
  if (record.detections.length === 0) {
    return '未见明显异常'
  }
  return record.detections.slice(0, 2).map((item) => item.class).join('、')
}

function getRouteImageId() {
  const value = route.query.image_id
  return Array.isArray(value) ? value[0] : value
}

watch(
  () => route.query.image_id,
  async () => {
    const imageId = getRouteImageId()
    if (!imageId || !canReadImages.value) {
      return
    }
    await fetchAnalysisRecord(imageId)
    const matched = records.value.find((item) => item.image_id === imageId)
    if (matched) {
      openDetail(matched)
    }
  },
)

onMounted(async () => {
  if (canReadImages.value) {
    await fetchRecords()
  }
})
</script>

<template>
  <div class="page-stack">
    <PageHeader
      title="诊断报告"
      description="查看历史诊断记录，支持详情预览、报告生成与下载。"
    />

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !canReadImages"
      title="当前账号暂无报告访问权限"
      description="查看诊断报告需要 `read:images` 权限。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <el-card v-else class="panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <span>历史诊断记录</span>
          <el-tag type="info">{{ recordsPagination.total }} 条</el-tag>
        </div>
      </template>

      <details class="compact-details">
        <summary>筛选条件</summary>
        <el-form label-position="top">
          <el-form-item label="患者编号">
            <el-input v-model="filters.patient_id" placeholder="按患者编号搜索" clearable />
          </el-form-item>
          <el-form-item label="影像类型">
            <el-select v-model="filters.image_type" class="w-full" clearable>
              <el-option label="全部" value="" />
              <el-option label="全景片" value="panoramic" />
              <el-option label="根尖片" value="periapical" />
              <el-option label="CBCT" value="cbct" />
            </el-select>
          </el-form-item>
          <el-form-item label="报告状态">
            <el-select v-model="filters.report_status" class="w-full" clearable>
              <el-option label="全部" value="" />
              <el-option label="诊断中" value="processing" />
              <el-option label="AI 已生成" value="ai_generated" />
              <el-option label="医生已审核" value="doctor_reviewed" />
              <el-option label="已完成" value="finalized" />
            </el-select>
          </el-form-item>
          <div class="actions">
            <el-button type="primary" @click="applyFilters">应用筛选</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
        </el-form>
      </details>

      <el-table :data="recordsWithIndex" stripe>
        <template #empty>
          <div class="empty-action-card">
            <strong>暂无报告记录</strong>
            <p>上传影像并完成 AI 分析后，报告会自动出现在这里。</p>
            <RouterLink to="/workspace" class="el-button el-button--primary"><span>上传影像</span></RouterLink>
          </div>
        </template>
        <el-table-column prop="rowNo" label="序号" width="80" />
        <el-table-column label="患者姓名" min-width="130">
          <template #default="scope">
            {{ scope.row.patient?.name ?? scope.row.patient_id }}
          </template>
        </el-table-column>
        <el-table-column label="影像类型" min-width="110">
          <template #default="scope">
            {{ getImageTypeLabel(scope.row.image_type) }}
          </template>
        </el-table-column>
        <el-table-column label="诊断时间" min-width="180">
          <template #default="scope">
            {{ new Date(scope.row.updated_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="诊断结果" min-width="170">
          <template #default="scope">
            {{ getResultText(scope.row) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="scope">
            <StatusTag :status="scope.row.report.status" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="scope">
            <el-button text @click="openDetail(scope.row)">查看详情</el-button>
            <el-button text @click="generateReport(scope.row)">生成报告</el-button>
            <el-button text @click="downloadClinicalReport(scope.row)">下载</el-button>
            <RouterLink :to="{ path: '/workspace', query: { image_id: scope.row.image_id } }" class="el-button is-text">
              <span>进入诊断</span>
            </RouterLink>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :current-page="Math.floor(recordsPagination.offset / recordsPagination.limit) + 1"
          :page-size="recordsPagination.limit"
          :page-sizes="[5, 10, 20, 50]"
          :total="recordsPagination.total"
          @current-change="handleRecordsPageChange"
          @size-change="handleRecordsPageSizeChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="detailVisible"
      title="报告详情"
      width="min(94vw, 760px)"
      :lock-scroll="false"
      modal-class="clinical-dialog-overlay"
    >
      <ReportPreview :record="selectedRecord" />
    </el-dialog>
  </div>
</template>
