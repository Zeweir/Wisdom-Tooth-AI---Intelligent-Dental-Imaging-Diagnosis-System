<script setup lang="ts">
import { computed } from 'vue'
import type { AnalysisFilters, AnalysisItem, PaginationMeta, ReportStatus } from '../types/analysis'
import { getImageTypeLabel, getReportStatusLabel, getReportStatusTagType } from '../utils/display'

const props = defineProps<{
  filters: AnalysisFilters
  records: AnalysisItem[]
  pagination: PaginationMeta
  selectedImageId: string
}>()

const emit = defineEmits<{
  select: [imageId: string]
  refresh: []
  applyFilters: []
  resetFilters: []
  pageChange: [page: number]
  pageSizeChange: [pageSize: number]
}>()

const finalizedCount = computed(() => props.records.filter((record) => record.report.status === 'finalized').length)
const pendingCount = computed(() => props.records.filter((record) => record.report.status !== 'finalized').length)
const statusPriority: Record<ReportStatus, number> = {
  processing: 0,
  ai_generated: 1,
  doctor_reviewed: 2,
  finalized: 3
}
const statusClassMap: Record<ReportStatus, string> = {
  processing: 'is-processing',
  ai_generated: 'needs-review',
  doctor_reviewed: 'needs-finalize',
  finalized: 'is-finalized'
}
const sortedRecords = computed(() =>
  [...props.records].sort((first, second) => {
    const priorityDiff = statusPriority[first.report.status] - statusPriority[second.report.status]
    if (priorityDiff !== 0) {
      return priorityDiff
    }
    return new Date(second.created_at).getTime() - new Date(first.created_at).getTime()
  })
)

function getQueueHint(record: AnalysisItem) {
  if (record.report.status === 'processing') {
    return '等待 AI 分析'
  }
  if (record.report.status === 'ai_generated') {
    return '需要医生审核'
  }
  if (record.report.status === 'doctor_reviewed') {
    return '等待正式确认'
  }
  return '已归档'
}
</script>

<template>
  <el-card class="panel" shadow="never">
    <template #header>
      <div class="panel-header">
        <span>分析记录</span>
        <el-button text @click="emit('refresh')">刷新</el-button>
      </div>
    </template>

    <div class="queue-summary">
      <span>{{ props.records.length }} 条记录</span>
      <span>{{ pendingCount }} 待确认</span>
      <span>{{ finalizedCount }} 正式报告</span>
    </div>

    <details class="compact-details">
      <summary>筛选病例</summary>
      <el-form label-position="top">
        <el-form-item label="患者">
          <el-input v-model="props.filters.patient_id" placeholder="按患者编号模糊搜索" clearable />
        </el-form-item>
        <el-form-item label="影像类型">
          <el-select v-model="props.filters.image_type" class="w-full" clearable>
            <el-option label="全部" value="" />
            <el-option label="全景片" value="panoramic" />
            <el-option label="根尖片" value="periapical" />
            <el-option label="CBCT" value="cbct" />
          </el-select>
        </el-form-item>
        <el-form-item label="报告状态">
          <el-select v-model="props.filters.report_status" class="w-full" clearable>
            <el-option label="全部" value="" />
            <el-option label="AI 已生成" value="ai_generated" />
            <el-option label="医生已审核" value="doctor_reviewed" />
            <el-option label="已正式确认" value="finalized" />
          </el-select>
        </el-form-item>
        <div class="actions">
          <el-button type="primary" @click="emit('applyFilters')">应用筛选</el-button>
          <el-button @click="emit('resetFilters')">重置</el-button>
        </div>
      </el-form>
    </details>

    <div v-if="props.records.length === 0" class="empty-action-card">
      <strong>暂无匹配病例</strong>
      <p>可以清空筛选条件，或上传新的牙科影像启动 AI 诊断。</p>
      <div class="quick-action-row">
        <el-button @click="emit('resetFilters')">清空筛选</el-button>
        <RouterLink to="/workspace" class="el-button el-button--primary"><span>上传影像</span></RouterLink>
      </div>
    </div>
    <div v-else class="record-list">
      <button
        v-for="record in sortedRecords"
        :key="record.image_id"
        class="record-item"
        :class="[statusClassMap[record.report.status], { active: props.selectedImageId === record.image_id }]"
        @click="emit('select', record.image_id)"
      >
        <div class="record-main">
          <strong>{{ record.patient?.name ?? record.patient_id }}</strong>
          <span>{{ getQueueHint(record) }}</span>
        </div>
        <div v-if="record.patient?.name" class="record-secondary">患者编号：{{ record.patient_id }}</div>
        <div class="record-secondary">{{ record.filename }}</div>
        <div class="record-meta">
          <el-tag size="small">{{ getImageTypeLabel(record.image_type) }}</el-tag>
          <el-tag size="small" :type="getReportStatusTagType(record.report.status)">{{ getReportStatusLabel(record.report.status) }}</el-tag>
        </div>
      </button>
    </div>

    <div class="pagination-row">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next"
        :current-page="Math.floor(props.pagination.offset / props.pagination.limit) + 1"
        :page-size="props.pagination.limit"
        :page-sizes="[5, 10, 20, 50]"
        :total="props.pagination.total"
        @current-change="emit('pageChange', $event)"
        @size-change="emit('pageSizeChange', $event)"
      />
    </div>
  </el-card>
</template>
