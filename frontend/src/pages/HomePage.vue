<script setup lang="ts">
import { computed, onMounted } from 'vue'

import PageHeader from '../components/PageHeader.vue'
import StatCard from '../components/StatCard.vue'
import StatusTag from '../components/StatusTag.vue'
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

const latestRecords = computed(() => records.value.slice(0, 8))
const pendingRecords = computed(() => records.value.filter((item) => item.report.status !== 'finalized').length)

const stats = computed(() => [
  {
    label: '今日诊断',
    value: records.value.length,
    description: '当前筛选条件下可见病例',
  },
  {
    label: '累计影像',
    value: dashboardSummary.value?.total_images ?? 0,
    description: '系统已接收的影像总量',
  },
  {
    label: '异常检出',
    value: dashboardSummary.value?.detection_count ?? 0,
    description: '累计检出的疑似病灶',
  },
  {
    label: '报告生成',
    value: dashboardSummary.value?.completed_images ?? 0,
    description: `待确认 ${pendingRecords.value} 条`,
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
    <PageHeader
      :title="`欢迎回来，${displayName || 'Dr.'}`"
      description="智齿 AI 将辅助你完成影像上传、诊断复核与报告管理。"
    >
      <template #actions>
        <RouterLink to="/upload" class="el-button el-button--primary"><span>快速上传影像</span></RouterLink>
      </template>
    </PageHeader>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !hasWorkbenchAccess"
      title="当前账号暂无工作台访问权限"
      description="请在 Logto 中为该用户分配 radiologist、doctor 或 chief_doctor 等角色后再重试。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <section v-else class="home-stats-grid">
      <StatCard
        v-for="item in stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :description="item.description"
      />
    </section>

    <el-card v-if="hasWorkbenchAccess" class="panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <span>最近诊断记录</span>
          <RouterLink to="/reports" class="el-button is-text"><span>查看全部</span></RouterLink>
        </div>
      </template>

      <el-empty v-if="latestRecords.length === 0" description="暂无诊断记录" />
      <el-table v-else :data="latestRecords" stripe>
        <el-table-column label="患者姓名" min-width="140">
          <template #default="scope">
            {{ scope.row.patient?.name ?? scope.row.patient_id }}
          </template>
        </el-table-column>
        <el-table-column label="影像类型" min-width="100">
          <template #default="scope">
            {{ getImageTypeLabel(scope.row.image_type) }}
          </template>
        </el-table-column>
        <el-table-column label="诊断状态" min-width="110">
          <template #default="scope">
            <StatusTag :status="scope.row.report.status" />
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="180">
          <template #default="scope">
            {{ new Date(scope.row.updated_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <RouterLink :to="{ path: '/diagnosis', query: { image_id: scope.row.image_id } }" class="el-button is-text">
              <span>查看诊断</span>
            </RouterLink>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
