<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useWorkbenchContext } from '../workbench'

const route = useRoute()
const workbench = useWorkbenchContext()
const navigationItems = workbench.navigationItems
const displayName = workbench.displayName
const displayedRoles = workbench.displayedRoles
const authScopes = workbench.authScopes
const authProfile = workbench.authProfile
const isAuthenticated = workbench.isAuthenticated
const isLoading = workbench.isLoading
const authReady = workbench.authReady
const beginSignIn = workbench.beginSignIn
const beginSignOut = workbench.beginSignOut

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
    <div class="page-shell dashboard-frame">
      <header class="topbar-card topbar-medical">
        <div class="topbar-main">
          <div class="brand-block">
            <div class="brand-icon" aria-hidden="true"><span>WT</span></div>
            <div>
              <p class="eyebrow">Wisdom Tooth AI</p>
              <h1>智齿 AI 医疗影像平台</h1>
            </div>
          </div>

          <nav class="top-nav" aria-label="主导航">
            <RouterLink
              v-for="item in navigationItems"
              :key="item.key"
              :to="item.to"
              class="top-nav-item"
              :class="{ active: currentNavKey === item.key }"
            >
              {{ item.shortLabel }}
            </RouterLink>
          </nav>
        </div>

        <div class="topbar-actions">
          <el-tag v-if="isAuthenticated" type="primary">{{ displayName || '已登录' }}</el-tag>
          <el-tag v-for="role in displayedRoles" :key="role.key" type="warning">{{ role.label }}</el-tag>
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
            当前角色：{{ displayedRoles.map((item) => item.label).join(', ') || '未匹配到预设角色' }}；权限数：{{ authScopes.length }}
          </summary>
          <div>{{ permissionSummary }}</div>
        </details>

        <RouterView />
      </main>
    </div>
  </div>
</template>
