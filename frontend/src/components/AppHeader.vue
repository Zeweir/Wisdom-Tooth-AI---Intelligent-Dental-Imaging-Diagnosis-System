<script setup lang="ts">
import { computed } from 'vue'
import { Bell, Search } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { useGlobalSearch } from '../composables/useGlobalSearch'
import { useWorkbenchContext } from '../workbench'
import { useAuth } from '../composables/useAuth'

const route = useRoute()
const router = useRouter()
const workbench = useWorkbenchContext()
const auth = useAuth()
const globalSearch = useGlobalSearch()

const pageTitle = computed(() => String(route.meta?.title ?? '工作台'))
const pageSubtitle = computed(() => String(route.meta?.subtitle ?? '牙齿影像智能诊断系统'))
const displayName = computed(() => auth.user.value?.display_name || '未登录用户')
const roleLabel = computed(() => auth.user.value?.role_label || '访客')

async function handleCommand(command: string | number | object) {
  if (command === 'signout') {
    auth.logout()
    window.location.replace('/login')
  }
}
</script>

<template>
  <header class="app-header">
    <div class="app-header-title">
      <h1>{{ pageTitle }}</h1>
      <p>{{ pageSubtitle }}</p>
    </div>

    <div class="app-header-search">
      <el-autocomplete
        v-model="globalSearch.keyword.value"
        :fetch-suggestions="globalSearch.fetchSuggestions"
        :loading="globalSearch.searching.value"
        placeholder="搜索患者、影像编号或文件名"
        clearable
        value-key="value"
        class="w-full"
        @select="globalSearch.openOption"
        @keyup.enter="globalSearch.submitSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #default="{ item }">
          <div class="global-search-option">
            <strong>{{ item.label }}</strong>
            <span>{{ item.caption }}</span>
          </div>
        </template>
      </el-autocomplete>
    </div>

    <div class="app-header-actions">
      <el-badge :value="0" class="app-header-bell" :hidden="true">
        <el-button circle>
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-badge>

      <el-button
        v-if="!auth.isAuthenticated.value"
        type="primary"
        :loading="auth.isLoading.value"
        @click="router.push('/login')"
      >
        登录
      </el-button>

      <el-dropdown v-else trigger="click" @command="handleCommand">
        <div class="app-header-user">
          <el-avatar size="small">{{ displayName.slice(0, 1) }}</el-avatar>
          <div class="app-header-user-meta">
            <strong>{{ displayName }}</strong>
            <span>{{ roleLabel }}</span>
          </div>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="signout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>
