<script setup lang="ts">
import { computed } from 'vue'

import { getImageTypeLabel, getReportStatusLabel } from '../utils/display'
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()
const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const hasWorkbenchAccess = workbench.hasWorkbenchAccess
const currentRecord = workbench.currentRecord
const records = workbench.records
const dashboardSummary = workbench.dashboardSummary
const beginSignOut = workbench.beginSignOut
const canReadImages = workbench.canReadImages

const pendingRecords = computed(() => records.value.filter((item) => item.report.status !== 'finalized'))
const latestRecords = computed(() => records.value.slice(0, 3))
const currentRecordLink = computed(() => currentRecord.value ? { path: '/workspace', query: { image_id: currentRecord.value.image_id } } : '/workspace')
const todayStats = computed(() => [
  {
    label: '待审核病例',
    value: pendingRecords.value.length,
    description: '优先处理未正式确认的报告',
  },
  {
    label: '患者档案',
    value: dashboardSummary.value?.total_patients ?? 0,
    description: `近 7 天新增 ${dashboardSummary.value?.recent_patients ?? 0} 位`,
  },
  {
    label: '处理中影像',
    value: dashboardSummary.value?.processing_images ?? records.value.filter((item) => item.status === 'processing').length,
    description: 'AI 分析仍在进行的任务',
  },
])
</script>

<template>
  <div class="page-stack">
    <section class="medical-hero-card doctor-home-hero">
      <div class="overview-copy">
        <div class="overview-pill">今日工作</div>
        <h2>先处理病例，再查看档案。</h2>
        <p>这里不展示复杂系统指标，只保留医生今天最常用的入口：进入工作站、继续审核当前病例、查看患者历史。</p>
        <div class="hero-actions">
          <RouterLink to="/workspace" class="el-button el-button--primary"><span>进入影像工作站</span></RouterLink>
          <RouterLink v-if="canReadImages" to="/patients" class="el-button is-plain"><span>患者档案</span></RouterLink>
        </div>
      </div>
      <div class="hero-summary-card">
        <div class="stats-grid compact-stats">
          <div v-for="item in todayStats" :key="item.label" class="stat-card medical-stat-card">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-desc">{{ item.description }}</div>
          </div>
        </div>
      </div>
    </section>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !hasWorkbenchAccess"
      title="当前账号暂无工作台访问权限"
      description="请在 Logto 中为该用户分配 radiologist、doctor 或 chief_doctor 等角色后再重试。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <section class="doctor-quick-grid">
      <el-card class="panel doctor-task-card" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>当前正在处理</span>
            <el-tag type="success" v-if="currentRecord">已选择</el-tag>
          </div>
        </template>
        <el-empty v-if="!currentRecord" description="暂无选中病例，进入工作站后会自动选择队列第一条" />
        <div v-else class="case-focus">
          <div>
            <strong>{{ currentRecord.patient?.name ?? currentRecord.patient_id }}</strong>
            <span>{{ getImageTypeLabel(currentRecord.image_type) }} / {{ currentRecord.filename }}</span>
          </div>
          <div class="case-focus-meta">
            <el-tag>{{ getReportStatusLabel(currentRecord.report.status) }}</el-tag>
            <el-tag type="success">{{ currentRecord.detections.length }} 个病灶</el-tag>
            <RouterLink :to="currentRecordLink" class="el-button el-button--primary is-plain"><span>继续审核</span></RouterLink>
          </div>
        </div>
      </el-card>

      <el-card class="panel doctor-task-card" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>最近病例</span>
            <RouterLink to="/workspace" class="el-button is-text"><span>查看全部</span></RouterLink>
          </div>
        </template>
        <div v-if="latestRecords.length > 0" class="simple-case-list">
          <RouterLink
            v-for="record in latestRecords"
            :key="record.image_id"
            :to="{ path: '/workspace', query: { image_id: record.image_id } }"
            class="simple-case-row"
          >
            <strong>{{ record.patient?.name ?? record.patient_id }}</strong>
            <span>{{ getImageTypeLabel(record.image_type) }} / {{ getReportStatusLabel(record.report.status) }}</span>
          </RouterLink>
        </div>
        <el-empty v-else description="暂无病例记录" />
      </el-card>
    </section>
  </div>
</template>
