<script setup lang="ts">
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()
const clinicalInsights = workbench.clinicalInsights
const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const hasWorkbenchAccess = workbench.hasWorkbenchAccess
const currentRecord = workbench.currentRecord
const beginSignOut = workbench.beginSignOut
</script>

<template>
  <div class="page-stack">
    <section class="medical-hero-card">
      <div class="overview-copy">
        <div class="overview-pill">口腔影像智能辅助诊断</div>
        <h2>清晰、可信的口腔影像医生工作台</h2>
        <p>聚焦病例上传、影像判读和报告审核。系统负责整理 AI 结果，医生负责最终确认。</p>
        <div class="hero-actions">
          <RouterLink to="/workspace" class="el-button el-button--primary"><span>进入影像工作站</span></RouterLink>
          <RouterLink to="/patients" class="el-button is-plain"><span>查看患者档案</span></RouterLink>
          <RouterLink to="/datasets" class="el-button is-plain"><span>数据集中心</span></RouterLink>
        </div>
      </div>
      <div class="hero-summary-card">
        <div class="stats-grid compact-stats">
          <div v-for="item in clinicalInsights" :key="item.label" class="stat-card medical-stat-card">
            <div class="stat-value">{{ item.value }}<span v-if="item.label === '平均置信度'">%</span></div>
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

    <section class="panel-grid single-panel-grid">
      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>当前病例</span>
            <el-tag type="success" v-if="currentRecord">已选择</el-tag>
          </div>
        </template>
        <el-empty v-if="!currentRecord" description="进入工作站后选择病例" />
        <div v-else class="case-focus">
          <div>
            <strong>{{ currentRecord.patient?.name ?? currentRecord.patient_id }}</strong>
            <span>{{ currentRecord.filename }}</span>
          </div>
          <div class="case-focus-meta">
            <el-tag>{{ currentRecord.image_type }}</el-tag>
            <el-tag type="success">{{ currentRecord.detections.length }} 个病灶</el-tag>
            <RouterLink to="/workspace" class="el-button el-button--primary is-plain"><span>继续审核</span></RouterLink>
          </div>
        </div>
      </el-card>
    </section>
  </div>
</template>
