<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { listReportRevisions } from '../api/analysis'
import type { PaginationMeta, ReportRevision } from '../types/analysis'
import { getReportStatusLabel, getReportStatusTagType } from '../utils/display'
import { downloadProtectedReportUrl } from '../utils/report'

const props = defineProps<{
  reportId: string | null
}>()

const visible = defineModel<boolean>('visible', { required: true })
const loading = ref(false)
const revisions = ref<ReportRevision[]>([])
const pagination = ref<PaginationMeta>({ limit: 10, offset: 0, total: 0 })

const currentPage = computed(() => Math.floor(pagination.value.offset / pagination.value.limit) + 1)

async function refreshRevisions() {
  if (!props.reportId || !visible.value) {
    revisions.value = []
    return
  }
  loading.value = true
  try {
    const result = await listReportRevisions(props.reportId, {
      limit: pagination.value.limit,
      offset: pagination.value.offset,
    })
    revisions.value = result.items
    pagination.value = result.meta
  } finally {
    loading.value = false
  }
}

async function handlePageChange(page: number) {
  pagination.value = {
    ...pagination.value,
    offset: (page - 1) * pagination.value.limit,
  }
  await refreshRevisions()
}

function downloadRevisionPdf(revision: ReportRevision) {
  if (!revision.pdf_url) {
    return
  }
  void downloadProtectedReportUrl(revision.pdf_url, `wisdom-tooth-report-revision-${revision.version_no}.pdf`)
}

watch(
  () => [visible.value, props.reportId],
  async () => {
    pagination.value = { ...pagination.value, offset: 0 }
    await refreshRevisions()
  }
)
</script>

<template>
  <el-drawer
    v-model="visible"
    title="报告版本历史"
    size="min(94vw, 620px)"
    :lock-scroll="false"
    modal-class="clinical-drawer-overlay"
  >
    <el-skeleton v-if="loading" :rows="5" animated />
    <el-empty v-else-if="revisions.length === 0" description="暂无报告版本记录，保存审核意见后会自动生成" />
    <div v-else class="revision-list">
      <article v-for="revision in revisions" :key="revision.revision_id" class="revision-card">
        <div class="panel-header">
          <span>V{{ revision.version_no }} / {{ getReportStatusLabel(revision.status) }}</span>
          <el-tag :type="getReportStatusTagType(revision.status)">{{ getReportStatusLabel(revision.status) }}</el-tag>
        </div>
        <div class="report-meta-strip">
          <span>操作者：{{ revision.actor_sub }}</span>
          <span>角色：{{ revision.actor_roles.join(', ') || '未记录' }}</span>
          <span>时间：{{ new Date(revision.created_at).toLocaleString() }}</span>
          <span>检测结果：{{ revision.detections.length }} 项</span>
        </div>
        <div class="patient-report-summary">
          <strong>医生意见</strong>
          <span>{{ revision.doctor_review || '暂无医生审核意见' }}</span>
        </div>
        <div class="record-meta">
          <el-tag v-if="revision.pdf_variant" type="info">{{ revision.pdf_variant }}</el-tag>
          <el-button v-if="revision.pdf_url" text @click="downloadRevisionPdf(revision)">下载版本 PDF</el-button>
        </div>
        <details class="compact-details">
          <summary>查看报告内容</summary>
          <p class="clinical-copy">{{ revision.structured_content.summary || revision.content }}</p>
        </details>
      </article>

      <div class="pagination-row">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :current-page="currentPage"
          :page-size="pagination.limit"
          :total="pagination.total"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </el-drawer>
</template>
