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

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function buildReportHtml(record: AnalysisItem) {
  const detections = record.detections
    .map((item) => `<tr><td>${escapeHtml(item.tooth_id)}</td><td>${escapeHtml(item.class)}</td><td>${escapeHtml(item.severity)}</td><td>${Math.round(item.confidence * 100)}%</td></tr>`)
    .join('')
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>智齿 AI 诊断报告 - ${escapeHtml(record.patient_id)}</title>
  <style>
    body { font-family: "Noto Sans SC", sans-serif; color: #0f172a; margin: 32px; line-height: 1.7; }
    h1 { color: #2563eb; }
    table { width: 100%; border-collapse: collapse; margin: 16px 0; }
    th, td { border: 1px solid #dbe3ef; padding: 8px; text-align: left; }
    th { background: #f8fafc; }
  </style>
</head>
<body>
  <h1>智齿 AI 牙齿影像智能诊断报告</h1>
  <p><strong>患者：</strong>${escapeHtml(record.patient?.name ?? record.patient_id)}（${escapeHtml(record.patient_id)}）</p>
  <p><strong>影像文件：</strong>${escapeHtml(record.filename)}</p>
  <p><strong>影像类型：</strong>${escapeHtml(record.image_type)}</p>
  <h2>AI 诊断内容</h2>
  <p>${escapeHtml(record.report.content || '暂无')}</p>
  <h2>医生审核意见</h2>
  <p>${escapeHtml(record.report.doctor_review || '暂无')}</p>
  <h2>检测明细</h2>
  <table>
    <thead><tr><th>牙位</th><th>类别</th><th>严重程度</th><th>置信度</th></tr></thead>
    <tbody>${detections}</tbody>
  </table>
</body>
</html>`
}

function downloadReport(record: AnalysisItem) {
  const html = buildReportHtml(record)
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `wisdom-tooth-report-${record.patient_id}.html`
  link.click()
  URL.revokeObjectURL(url)
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
            <el-button text @click="downloadReport(scope.row)">下载</el-button>
            <RouterLink :to="{ path: '/diagnosis', query: { image_id: scope.row.image_id } }" class="el-button is-text">
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
