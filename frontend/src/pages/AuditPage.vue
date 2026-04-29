<script setup lang="ts">
import { computed, onMounted } from 'vue'

import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()
const canViewAuditLogs = workbench.canViewAuditLogs
const auditLogs = workbench.auditLogs
const auditFilters = workbench.auditFilters
const auditPagination = workbench.auditPagination
const refreshAuditLogs = workbench.refreshAuditLogs
const applyAuditFilters = workbench.applyAuditFilters
const resetAuditFilters = workbench.resetAuditFilters
const handleAuditPageChange = workbench.handleAuditPageChange
const handleAuditPageSizeChange = workbench.handleAuditPageSizeChange
const quickAuditFilters = [
  { label: '报告审核', action: 'report.reviewed', resourceType: 'report' },
  { label: '正式确认', action: 'report.finalized', resourceType: 'report' },
  { label: '数据集导入', action: 'dataset_import.created', resourceType: 'dataset_import' },
  { label: '患者更新', action: 'patient.updated', resourceType: 'patient' },
  { label: '影像上传', action: 'image.uploaded', resourceType: 'image' },
]
const latestAuditLogs = computed(() => auditLogs.value.slice(0, 5).map((log, index) => ({
  ...log,
  index: String(index + 1).padStart(2, '0'),
  detailText: JSON.stringify(log.detail),
  actionLabel: getAuditActionLabel(log.action)
})))

function getAuditActionLabel(action: string) {
  const labels: Record<string, string> = {
    'report.reviewed': '报告审核',
    'report.finalized': '正式确认',
    'dataset_import.created': '数据导入',
    'dataset_import.split': '训练集划分',
    'dataset.seeded': '公开清单初始化',
    'dataset.created': '数据集登记',
    'dataset.updated': '数据集更新',
    'patient.created': '新建患者',
    'patient.updated': '患者更新',
    'image.uploaded': '影像上传',
  }
  return labels[action] ?? action
}

async function applyQuickAuditFilter(item: { action: string; resourceType: string }) {
  auditFilters.value.action = item.action
  auditFilters.value.resource_type = item.resourceType
  auditFilters.value.resource_id = ''
  auditFilters.value.actor_sub = ''
  await applyAuditFilters()
}

onMounted(async () => {
  await refreshAuditLogs()
})
</script>

<template>
  <div class="page-stack">
    <section class="medical-page-header">
      <div>
        <div class="overview-pill">审计中心</div>
        <h2>关键操作留痕与事件追踪</h2>
        <p>围绕上传、分析、审核和正式确认过程，集中展示审计日志。</p>
      </div>
      <el-button text @click="refreshAuditLogs">刷新日志</el-button>
    </section>

    <UnauthorizedPanel
      v-if="!canViewAuditLogs"
      title="当前角色不可查看审计中心"
      description="如需查看关键留痕，请为当前用户分配 audit 菜单对应权限。"
    />

    <div v-else class="audit-grid">
      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>最近关键事件</span>
            <el-tag type="info">{{ latestAuditLogs.length }} 条</el-tag>
          </div>
        </template>

        <el-empty v-if="latestAuditLogs.length === 0" description="暂无审计日志" />
        <div v-else class="audit-timeline">
          <div v-for="log in latestAuditLogs" :key="log.audit_log_id" class="audit-card">
            <div class="audit-card-header">
              <div class="audit-icon">{{ log.index }}</div>
              <div class="audit-main">
                <strong>{{ log.actionLabel }}</strong>
                <div class="audit-time">{{ log.created_at }}</div>
              </div>
              <el-tag type="success">{{ log.resource_type }}</el-tag>
            </div>
            <div class="audit-detail">{{ log.detailText }}</div>
          </div>
        </div>
      </el-card>

      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>关键审计日志</span>
            <el-tag type="info">{{ auditLogs.length }} 条</el-tag>
          </div>
        </template>

        <el-table :data="auditLogs" stripe>
          <el-table-column prop="created_at" label="时间" min-width="180" />
          <el-table-column prop="action" label="动作" min-width="160" />
          <el-table-column prop="resource_type" label="资源类型" min-width="120" />
          <el-table-column prop="resource_id" label="资源 ID" min-width="180" />
          <el-table-column prop="actor_sub" label="操作者" min-width="220" />
          <el-table-column label="详情" min-width="320">
            <template #default="scope">
              {{ JSON.stringify(scope.row.detail) }}
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-row">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next"
            :current-page="Math.floor(auditPagination.offset / auditPagination.limit) + 1"
            :page-size="auditPagination.limit"
            :page-sizes="[5, 10, 20, 50]"
            :total="auditPagination.total"
            @current-change="handleAuditPageChange"
            @size-change="handleAuditPageSizeChange"
          />
        </div>
      </el-card>
    </div>

    <el-card v-if="canViewAuditLogs" class="panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <span>审计高级筛选</span>
          <el-tag type="success">分页查询</el-tag>
        </div>
      </template>

      <el-form class="audit-filter-form" label-position="top">
        <div class="audit-quick-filters">
          <span>快捷筛选</span>
          <el-button
            v-for="item in quickAuditFilters"
            :key="item.action"
            plain
            @click="applyQuickAuditFilter(item)"
          >
            {{ item.label }}
          </el-button>
        </div>
        <el-form-item label="动作">
          <el-input v-model="auditFilters.action" placeholder="例如 image.uploaded" clearable />
        </el-form-item>
        <el-form-item label="资源类型">
          <el-select v-model="auditFilters.resource_type" class="w-full" clearable>
            <el-option label="全部" value="" />
            <el-option label="影像 image" value="image" />
            <el-option label="报告 report" value="report" />
            <el-option label="患者 patient" value="patient" />
            <el-option label="数据集 dataset" value="dataset" />
            <el-option label="数据导入 dataset_import" value="dataset_import" />
          </el-select>
        </el-form-item>
        <el-form-item label="资源 ID">
          <el-input v-model="auditFilters.resource_id" placeholder="按资源 ID 精确筛选" clearable />
        </el-form-item>
        <el-form-item label="操作者">
          <el-input v-model="auditFilters.actor_sub" placeholder="按操作者 sub 模糊筛选" clearable />
        </el-form-item>
        <div class="actions audit-filter-actions">
          <el-button type="primary" @click="applyAuditFilters">应用筛选</el-button>
          <el-button @click="resetAuditFilters">重置</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>
