<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useWorkbenchContext } from '../workbench'

const route = useRoute()
const workbench = useWorkbenchContext()
const navigationItems = workbench.navigationItems
const visibleMenus = workbench.visibleMenus
const displayName = workbench.displayName
const displayedRoles = workbench.displayedRoles
const authScopes = workbench.authScopes
const records = workbench.records
const currentRecord = workbench.currentRecord
const auditLogs = workbench.auditLogs
const isAuthenticated = workbench.isAuthenticated
const isLoading = workbench.isLoading
const authReady = workbench.authReady
const beginSignIn = workbench.beginSignIn
const beginSignOut = workbench.beginSignOut

const currentNavKey = computed(() => {
  const current = navigationItems.value.find((item) => item.to === route.path)
  return current?.key ?? 'home'
})
</script>

<template>
  <div class="dashboard-shell">
    <div class="dashboard-backdrop" />
    <div class="page-shell dashboard-frame">
      <header class="topbar-card topbar-medical">
        <div class="brand-block">
          <div class="brand-icon" aria-hidden="true"><span>WT</span></div>
          <div>
            <p class="eyebrow">Wisdom Tooth AI Clinical Suite</p>
            <h1>智齿 AI 医疗影像平台</h1>
            <p class="hero-desc">面向口腔影像诊断、AI 辅助分析、医生审核和审计追踪的一体化医疗工作台。</p>
          </div>
        </div>
        <div class="topbar-actions">
          <el-tag type="success" size="large">医疗影像工作台</el-tag>
          <el-tag v-if="isAuthenticated" type="primary">{{ displayName || '已登录' }}</el-tag>
          <el-tag v-for="role in displayedRoles" :key="role.key" type="warning">{{ role.label }}</el-tag>
          <el-button v-if="!isAuthenticated" type="primary" :loading="isLoading" @click="beginSignIn">使用 Logto 登录</el-button>
          <el-button v-else @click="beginSignOut">退出登录</el-button>
        </div>
      </header>

      <div class="workspace-layout">
        <aside class="sidebar-card medical-sidebar">
          <div class="sidebar-section">
            <div class="sidebar-title">临床导航</div>
            <RouterLink
              v-for="item in navigationItems"
              :key="item.key"
              :to="item.to"
              class="nav-item nav-link"
              :class="{ active: currentNavKey === item.key }"
            >
              <span class="nav-label">{{ item.label }}</span>
              <span class="nav-caption">{{ item.caption }}</span>
            </RouterLink>
          </div>

          <div class="sidebar-section sidebar-summary">
            <div class="sidebar-title">当前账号</div>
            <div class="sidebar-user">{{ isAuthenticated ? (displayName || '已登录用户') : '未登录' }}</div>
            <div class="sidebar-tags">
              <el-tag v-for="menu in visibleMenus" :key="menu.key" effect="plain">{{ menu.label }}</el-tag>
            </div>
            <div class="sidebar-hint">
              {{ isAuthenticated ? `权限数：${authScopes.length} / 角色数：${displayedRoles.length}` : '登录后可查看临床工作台、权限与审计模块' }}
            </div>
          </div>

          <div class="sidebar-section sidebar-metric-box">
            <div class="sidebar-title">病例摘要</div>
            <div class="sidebar-metrics">
              <div class="sidebar-metric">
                <span>病例</span>
                <strong>{{ records.length }}</strong>
              </div>
              <div class="sidebar-metric">
                <span>病灶</span>
                <strong>{{ currentRecord?.detections.length ?? 0 }}</strong>
              </div>
              <div class="sidebar-metric">
                <span>日志</span>
                <strong>{{ auditLogs.length }}</strong>
              </div>
            </div>
          </div>
        </aside>

        <main class="content-stack medical-content">
          <el-alert
            v-if="!isAuthenticated && authReady"
            title="请先登录后再访问影像工作站、权限中心与审计功能"
            type="info"
            :closable="false"
            show-icon
            class="surface-alert"
          />

          <el-alert
            v-else-if="isAuthenticated && authReady"
            :title="`当前角色：${displayedRoles.map((item) => item.label).join(', ') || '未匹配到预设角色'}；当前权限：${authScopes.join(', ') || '无 API scope'}`"
            type="success"
            :closable="false"
            show-icon
            class="surface-alert"
          />

          <RouterView />
        </main>
      </div>
    </div>
  </div>
</template>
