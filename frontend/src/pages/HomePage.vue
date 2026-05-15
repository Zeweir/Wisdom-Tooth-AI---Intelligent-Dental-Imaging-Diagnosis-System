<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

const STATUS_LABELS: Record<string, string> = {
  processing: '处理中',
  ai_generated: '待审核',
  doctor_reviewed: '已审核',
  finalized: '已归档',
}
import {
  Upload,
  DataAnalysis,
  Document,
  User,
  Files,
  TrendCharts,
  Plus,
  Search,
} from '@element-plus/icons-vue'
import ChartPanel from '../components/ChartPanel.vue'
import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import { getImageTypeLabel } from '../utils/display'
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()

const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const hasWorkbenchAccess = workbench.hasWorkbenchAccess
const records = workbench.records
const dashboardSummary = workbench.dashboardSummary
const beginSignOut = workbench.beginSignOut
const canReadImages = workbench.canReadImages
const fetchRecords = workbench.fetchRecords
const displayName = workbench.displayName
const canUpload = workbench.canUpload

const latestRecords = computed(() => records.value.slice(0, 6))
const pendingRecords = computed(() => records.value.filter((item) => item.report.status !== 'finalized').length)

// Report status distribution pie chart
const reportStatusOption = computed(() => {
  const statusMap = dashboardSummary.value?.report_status_counts ?? {}
  const nameMap: Record<string, string> = {
    processing: '处理中',
    ai_generated: 'AI 已生成',
    doctor_reviewed: '已审核',
    finalized: '已归档',
  }
  const colorMap: Record<string, string> = {
    processing: '#e6a23c',
    ai_generated: '#409eff',
    doctor_reviewed: '#67c23a',
    finalized: '#909399',
  }
  const data = Object.entries(statusMap).map(([key, value]) => ({
    name: nameMap[key] ?? key,
    value,
    itemStyle: { color: colorMap[key] ?? '#ccc' },
  }))
  return {
    tooltip: { trigger: 'item' as const },
    legend: { bottom: '0%' },
    series: [{
      type: 'pie' as const,
      radius: ['45%', '75%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { label: { show: true, fontWeight: 'bold', fontSize: 16 } },
      data,
    }],
  }
})

// Image type distribution bar chart
const imageTypeOption = computed(() => {
  const typeMap = dashboardSummary.value?.image_type_counts ?? {}
  const nameMap: Record<string, string> = {
    panoramic: '全景片',
    periapical: '根尖片',
    cbct: 'CBCT',
  }
  return {
    tooltip: { trigger: 'axis' as const },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category' as const, data: Object.keys(typeMap).map((k) => nameMap[k] ?? k) },
    yAxis: { type: 'value' as const },
    series: [{
      type: 'bar' as const,
      data: Object.values(typeMap),
      itemStyle: {
        color: '#409eff',
        borderRadius: [4, 4, 0, 0],
      },
    }],
  }
})

// Monthly trend mock (based on available data)
const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' as const },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category' as const,
    data: ['1月', '2月', '3月', '4月', '5月'],
  },
  yAxis: { type: 'value' as const },
  series: [
    {
      name: '上传量',
      type: 'line' as const,
      data: [0, 0, 0, 3, records.value.length],
      smooth: true,
      itemStyle: { color: '#409eff' },
    },
    {
      name: '已完成',
      type: 'line' as const,
      data: [0, 0, 0, 2, dashboardSummary.value?.completed_images ?? 0],
      smooth: true,
      itemStyle: { color: '#67c23a' },
    },
  ],
}))

const topStats = computed(() => [
  {
    label: '总影像数',
    value: dashboardSummary.value?.total_images ?? 0,
    icon: Files,
    color: '#409eff',
  },
  {
    label: '总患者',
    value: dashboardSummary.value?.total_patients ?? 0,
    icon: User,
    color: '#67c23a',
  },
  {
    label: '检出病灶',
    value: dashboardSummary.value?.detection_count ?? 0,
    icon: Search,
    color: '#e6a23c',
  },
  {
    label: '待确认',
    value: pendingRecords.value,
    icon: DataAnalysis,
    color: '#f56c6c',
  },
])

const quickActions = computed(() => [
  {
    label: '上传影像',
    desc: '上传牙科影像并启动 AI 分析',
    icon: Upload,
    to: '/workspace',
    color: '#409eff',
    visible: canUpload.value,
  },
  {
    label: '患者管理',
    desc: '查询和管理患者档案',
    icon: User,
    to: '/patients',
    color: '#67c23a',
    visible: canReadImages.value,
  },
  {
    label: '数据集中心',
    desc: '公开牙科数据集与模型评估',
    icon: Files,
    to: '/datasets',
    color: '#e6a23c',
    visible: canReadImages.value,
  },
  {
    label: '审计日志',
    desc: '关键操作留痕追踪',
    icon: Document,
    to: '/audit',
    color: '#909399',
    visible: workbench.canViewAuditLogs.value,
  },
])

onMounted(async () => {
  if (canReadImages.value) {
    await fetchRecords()
  }
})
</script>

<template>
  <div class="page-stack">
    <!-- Welcome Banner -->
    <div class="home-hero">
      <div class="home-hero-content">
        <h1>欢迎回来，{{ displayName }}</h1>
        <p>智齿 AI 辅助你完成影像上传、AI 诊断复核与报告管理</p>
        <RouterLink v-if="canUpload" to="/workspace" class="el-button el-button--primary el-button--large">
          <el-icon><Plus /></el-icon>
          <span>快速上传影像</span>
        </RouterLink>
      </div>
      <div class="home-hero-icon">
        <TrendCharts style="font-size: 80px; opacity: 0.3" />
      </div>
    </div>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !hasWorkbenchAccess"
      title="当前账号暂无工作台访问权限"
      description="请联系管理员为您分配相应角色后再重试。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <!-- Top Stats Row -->
    <div class="home-stats-row">
      <div
        v-for="stat in topStats"
        :key="stat.label"
        class="home-stat-card"
      >
        <div class="home-stat-icon" :style="{ background: stat.color + '20', color: stat.color }">
          <el-icon><component :is="stat.icon" /></el-icon>
        </div>
        <div class="home-stat-body">
          <strong>{{ stat.value }}</strong>
          <span>{{ stat.label }}</span>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="home-section">
      <h3 class="home-section-title">快捷入口</h3>
      <div class="home-actions-grid">
        <RouterLink
          v-for="action in quickActions.filter((a) => a.visible)"
          :key="action.label"
          :to="action.to"
          class="home-action-card"
        >
          <div class="home-action-icon" :style="{ background: action.color + '18', color: action.color }">
            <el-icon :size="22"><component :is="action.icon" /></el-icon>
          </div>
          <div class="home-action-body">
            <strong>{{ action.label }}</strong>
            <span>{{ action.desc }}</span>
          </div>
        </RouterLink>
      </div>
    </div>

    <!-- Charts Row -->
    <div v-if="hasWorkbenchAccess" class="home-charts-grid">
      <el-card class="panel" shadow="never">
        <template #header>
          <span class="panel-title">报告状态分布</span>
        </template>
        <ChartPanel :option="reportStatusOption" height="280px" />
      </el-card>

      <el-card class="panel" shadow="never">
        <template #header>
          <span class="panel-title">影像类型分布</span>
        </template>
        <ChartPanel :option="imageTypeOption" height="280px" />
      </el-card>

      <el-card class="panel home-chart-full" shadow="never">
        <template #header>
          <span class="panel-title">诊疗趋势</span>
        </template>
        <ChartPanel :option="trendOption" height="280px" />
      </el-card>
    </div>

    <!-- Recent Records -->
    <el-card v-if="hasWorkbenchAccess" class="panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <span class="panel-title">最近诊断记录</span>
          <RouterLink to="/workspace" class="el-button el-button--text">查看全部 →</RouterLink>
        </div>
      </template>

      <div v-if="latestRecords.length === 0" class="empty-action-card">
        <el-icon :size="48" color="#c0c4cc"><DataAnalysis /></el-icon>
        <strong>还没有诊断记录</strong>
        <p>上传一张牙科影像，系统会自动完成 AI 分析并生成报告草稿。</p>
        <RouterLink to="/workspace" class="el-button el-button--primary">开始上传</RouterLink>
      </div>
      <el-table v-else :data="latestRecords" stripe class="home-table">
        <el-table-column label="患者" min-width="140">
          <template #default="scope">
            <span v-if="scope.row.patient?.name">{{ scope.row.patient.name }}</span>
            <code v-else>{{ scope.row.patient_id }}</code>
          </template>
        </el-table-column>
        <el-table-column label="影像类型" min-width="100">
          <template #default="scope">
            <el-tag size="small">{{ getImageTypeLabel(scope.row.image_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="文件名" min-width="160">
          <template #default="scope">
            <span class="text-ellipsis">{{ scope.row.filename }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="110">
          <template #default="scope">
            <el-tag
              :type="scope.row.report.status === 'finalized' ? 'success' : scope.row.report.status === 'ai_generated' ? 'warning' : 'info'"
              size="small"
            >
              {{ STATUS_LABELS[scope.row.report.status] ?? scope.row.report.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="170">
          <template #default="scope">
            {{ new Date(scope.row.updated_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <RouterLink
              :to="{ path: '/workspace', query: { image_id: scope.row.image_id } }"
              class="el-button el-button--small el-button--primary is-plain"
            >
              查看详情
            </RouterLink>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.home-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: #fff;
  margin-bottom: 20px;
}

.home-hero-content h1 {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 6px;
}

.home-hero-content p {
  font-size: 14px;
  opacity: 0.9;
  margin: 0 0 16px;
}

.home-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.home-stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.home-stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  font-size: 20px;
}

.home-stat-body strong {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.home-stat-body span {
  font-size: 12px;
  color: #909399;
}

.home-section { margin-bottom: 20px; }

.home-section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px;
}

.home-actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.home-action-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  background: #fff;
  border-radius: 10px;
  text-decoration: none;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: transform 0.15s, box-shadow 0.15s;
}

.home-action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.home-action-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 10px;
}

.home-action-body strong {
  display: block;
  font-size: 14px;
  color: #303133;
}

.home-action-body span {
  font-size: 12px;
  color: #909399;
}

.home-charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.home-chart-full { grid-column: 1 / -1; }

.panel-title {
  font-size: 15px;
  font-weight: 600;
}

.home-table :deep(.el-table__header th) {
  background: #fafafa;
  color: #606266;
  font-weight: 600;
}

.empty-action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  gap: 10px;
  color: #909399;
}

.empty-action-card strong { font-size: 16px; color: #606266; }
.empty-action-card p { font-size: 13px; margin: 0; }

.text-ellipsis {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

@media (max-width: 1200px) {
  .home-stats-row, .home-actions-grid { grid-template-columns: repeat(2, 1fr); }
  .home-charts-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .home-stats-row, .home-actions-grid { grid-template-columns: 1fr; }
  .home-hero { flex-direction: column; text-align: center; }
}
</style>
