<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useWorkbenchContext } from '../workbench'

const route = useRoute()
const workbench = useWorkbenchContext()
const navigationItems = workbench.navigationItems
const displayName = workbench.displayName
const displayedRoles = workbench.displayedRoles
const authProfile = workbench.authProfile
const isAuthenticated = workbench.isAuthenticated
const isLoading = workbench.isLoading
const authReady = workbench.authReady
const canViewAccessPanel = workbench.canViewAccessPanel
const canViewAuditLogs = workbench.canViewAuditLogs
const beginSignIn = workbench.beginSignIn
const beginSignOut = workbench.beginSignOut

const primaryNavigationItems = computed(() => navigationItems.value.filter((item) => item.key !== 'system'))
const systemNavigationItem = computed(() => navigationItems.value.find((item) => item.key === 'system'))

const currentNavKey = computed(() => {
  if (route.path === '/access' || route.path === '/audit') {
    return 'system'
  }
  const current = navigationItems.value.find((item) => item.to === route.path)
  return current?.key ?? 'home'
})

const permissionSummary = computed(() => {
  const permissions = authProfile.value?.permissions ?? []
  if (permissions.length === 0) {
    return '未检测到 API 权限'
  }
  return `权限：${permissions.join(', ')}`
})
</script>

<template>
  <div class="dashboard-shell">
    <a class="skip-link" href="#main-content">跳到主内容</a>
    <div class="dashboard-backdrop" />
    <div class="clinical-shell dashboard-frame">
      <aside class="clinical-sidebar" aria-label="临床工作台导航">
        <RouterLink to="/" class="brand-block sidebar-brand" aria-label="返回临床总览">
          <div class="brand-block">
            <div class="brand-icon" aria-hidden="true"><span>WT</span></div>
            <div>
              <p class="eyebrow">Wisdom Tooth AI</p>
              <h1>智齿 AI 医疗影像平台</h1>
            </div>
          </div>
        </RouterLink>

        <div class="sidebar-section">
          <span>临床工作区</span>
          <nav class="side-nav" aria-label="主导航">
            <RouterLink
              v-for="item in primaryNavigationItems"
              :key="item.key"
              :to="item.to"
              class="side-nav-item"
              :class="{ active: currentNavKey === item.key }"
            >
              <strong>{{ item.label }}</strong>
              <small>{{ item.caption }}</small>
            </RouterLink>
          </nav>
        </div>

        <div v-if="systemNavigationItem" class="sidebar-section">
          <span>权限审计</span>
          <nav class="side-nav compact-side-nav" aria-label="系统导航">
            <RouterLink
              v-if="canViewAccessPanel"
              to="/access"
              class="side-nav-item"
              :class="{ active: route.path === '/access' }"
            >
              <strong>权限中心</strong>
              <small>角色职责与可执行动作</small>
            </RouterLink>
            <RouterLink
              v-if="canViewAuditLogs"
              to="/audit"
              class="side-nav-item"
              :class="{ active: route.path === '/audit' }"
            >
              <strong>审计中心</strong>
              <small>关键操作留痕</small>
            </RouterLink>
          </nav>
        </div>

        <div class="sidebar-footnote">
          <strong>医生审核优先</strong>
          <span>AI 结果仅作为辅助诊断，正式报告需医生确认。</span>
        </div>
      </aside>

      <div class="clinical-main">
        <header class="clinical-topbar">
          <div>
            <p class="eyebrow">Clinical Console</p>
            <h2>医生临床工作台</h2>
          </div>

          <div class="topbar-actions">
            <el-tag v-if="isAuthenticated" type="primary">{{ displayName || '已登录' }}</el-tag>
            <el-tag v-if="displayedRoles[0]" type="warning">{{ displayedRoles[0].label }}</el-tag>
            <el-button v-if="!isAuthenticated" type="primary" :loading="isLoading" @click="beginSignIn">登录</el-button>
            <el-button v-else @click="beginSignOut">退出</el-button>
          </div>
        </header>

        <main id="main-content" class="content-stack medical-content" tabindex="-1">
          <el-alert
            v-if="!isAuthenticated && authReady"
            title="请先登录后再访问影像工作站、权限中心与审计功能"
            type="info"
            :closable="false"
            show-icon
            class="surface-alert"
          />

          <details v-else-if="isAuthenticated && authReady" class="debug-permission-panel">
            <summary>
              账号权限状态
            </summary>
            <div>{{ permissionSummary }}</div>
          </details>

          <RouterView />
        </main>
      </div>
    </div>
  </div>
</template>
