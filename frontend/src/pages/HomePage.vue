<script setup lang="ts">
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()
const dashboardStats = workbench.dashboardStats
const clinicalInsights = workbench.clinicalInsights
const dashboardSummary = workbench.dashboardSummary
const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const hasWorkbenchAccess = workbench.hasWorkbenchAccess
const displayName = workbench.displayName
const displayedRoles = workbench.displayedRoles
const visibleMenus = workbench.visibleMenus
const currentRecord = workbench.currentRecord
const beginSignOut = workbench.beginSignOut
const imageTypeLabels: Record<string, string> = {
  panoramic: '全景片',
  periapical: '根尖片',
  cbct: 'CBCT'
}

const clinicalFlows = [
  {
    index: '01',
    title: '影像接入',
    description: '采集全景片、根尖片或 CBCT 后进入统一病例队列。'
  },
  {
    index: '02',
    title: 'AI 初筛',
    description: '自动识别牙位、病灶类别、严重程度与置信度。'
  },
  {
    index: '03',
    title: '医生复核',
    description: '医生基于影像和 AI 结果补充诊断意见。'
  },
  {
    index: '04',
    title: '报告留痕',
    description: '正式确认前保留审核意见、操作记录和审计事件。'
  }
]
</script>

<template>
  <div class="page-stack">
    <section class="medical-hero-card">
      <div class="overview-copy">
        <div class="overview-pill">口腔影像智能辅助诊断</div>
        <h2>面向口腔影像诊断的医生工作台入口</h2>
        <p>
          从病例接入、AI 辅助判读、医生审核到审计追踪，首页优先呈现医生当班需要关注的状态和下一步动作。
        </p>
        <div class="hero-actions">
          <RouterLink to="/workspace" class="el-button el-button--primary"><span>进入影像工作站</span></RouterLink>
          <RouterLink to="/access" class="el-button is-plain"><span>查看权限模型</span></RouterLink>
        </div>
      </div>
      <div class="stats-grid">
        <div v-for="stat in dashboardStats" :key="stat.label" class="stat-card medical-stat-card">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-desc">{{ stat.description }}</div>
        </div>
      </div>
    </section>

    <section class="ops-grid">
      <el-card class="panel command-card" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>今日工作台摘要</span>
            <el-tag type="success">实时派生</el-tag>
          </div>
        </template>
        <div class="ops-metrics">
          <div v-for="item in clinicalInsights" :key="item.label" class="clinical-metric">
            <div class="metric-value">{{ item.value }}<span v-if="item.label === '平均置信度'">%</span></div>
            <div class="metric-label">{{ item.label }}</div>
            <div class="stat-desc">{{ item.description }}</div>
          </div>
        </div>
      </el-card>

      <el-card class="panel command-card" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>影像类型分布</span>
            <el-tag type="info">病例结构</el-tag>
          </div>
        </template>
        <div v-if="dashboardSummary" class="modality-bars">
          <div v-for="(count, type) in dashboardSummary.image_type_counts" :key="type" class="modality-row">
            <span>{{ imageTypeLabels[type] }}</span>
            <el-progress
              :percentage="dashboardSummary.total_images ? Math.round((count / dashboardSummary.total_images) * 100) : 0"
              :stroke-width="10"
            />
            <strong>{{ count }}</strong>
          </div>
        </div>
        <el-empty v-else description="登录并加载病例后显示影像类型分布" />
      </el-card>
    </section>

    <section class="clinical-flow-grid">
      <el-card v-for="flow in clinicalFlows" :key="flow.index" class="panel flow-card" shadow="never">
        <div class="flow-index">{{ flow.index }}</div>
        <h3>{{ flow.title }}</h3>
        <p>{{ flow.description }}</p>
      </el-card>
    </section>

    <section class="feature-grid">
      <el-card class="panel feature-card" shadow="never">
        <div class="feature-icon">IMG</div>
        <h3>影像接入</h3>
        <p>上传全景片、根尖片和 CBCT，进入统一分析流程。</p>
      </el-card>
      <el-card class="panel feature-card" shadow="never">
        <div class="feature-icon">REV</div>
        <h3>报告审核</h3>
        <p>AI 初稿、医生意见与正式确认拆分得更清楚。</p>
      </el-card>
      <el-card class="panel feature-card" shadow="never">
        <div class="feature-icon">RBAC</div>
        <h3>权限模型</h3>
        <p>集中展示角色来源、菜单可见性和 Logto Claim 对齐。</p>
      </el-card>
      <el-card class="panel feature-card" shadow="never">
        <div class="feature-icon">LOG</div>
        <h3>审计追踪</h3>
        <p>关键动作留痕便于回溯上传、审核和自动分析过程。</p>
      </el-card>
    </section>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !hasWorkbenchAccess"
      title="当前账号暂无工作台访问权限"
      description="请在 Logto 中为该用户分配 radiologist、doctor 或 chief_doctor 等角色后再重试。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <section class="panel-grid">
      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>临床概况</span>
            <el-tag type="info">首页总览</el-tag>
          </div>
        </template>
        <div class="overview-list">
          <div class="overview-list-item">
            <strong>当前登录</strong>
            <span>{{ isAuthenticated ? (displayName || '已登录用户') : '未登录' }}</span>
          </div>
          <div class="overview-list-item">
            <strong>当前角色</strong>
            <span>{{ displayedRoles.map((item) => item.label).join(', ') || '未匹配到预设角色' }}</span>
          </div>
          <div class="overview-list-item">
            <strong>当前可用模块</strong>
            <span>{{ visibleMenus.map((item) => item.label).join('、') || '暂无可见模块' }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>当前病例焦点</span>
            <el-tag type="success" v-if="currentRecord">{{ currentRecord.report.status }}</el-tag>
          </div>
        </template>
        <el-empty v-if="!currentRecord" description="当前还没有选中的病例记录" />
        <div v-else class="report-box">
          <div class="sub-title">病例信息</div>
          <p>患者：{{ currentRecord.patient_id }}</p>
          <p>影像：{{ currentRecord.filename }}</p>
          <p>类型：{{ currentRecord.image_type }}</p>
          <p>病灶数：{{ currentRecord.detections.length }}</p>
        </div>
      </el-card>
    </section>
  </div>
</template>
