<script setup lang="ts">
import { computed, ref } from 'vue'
import { Bell, Search } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'

import { useWorkbenchContext } from '../workbench'

const route = useRoute()
const workbench = useWorkbenchContext()
const searchKeyword = ref('')

const pageTitle = computed(() => String(route.meta?.title ?? '工作台'))
const pageSubtitle = computed(() => String(route.meta?.subtitle ?? '牙齿影像智能诊断系统'))
const displayName = computed(() => workbench.displayName.value || '未登录用户')
const roleLabel = computed(() => workbench.displayedRoles.value[0]?.label || '访客')

async function handleCommand(command: string | number | object) {
  if (command === 'signout') {
    await workbench.beginSignOut()
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
      <el-input v-model="searchKeyword" placeholder="搜索患者编号、影像编号（预留）" clearable>
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div class="app-header-actions">
      <el-badge :value="0" class="app-header-bell" :hidden="true">
        <el-button circle>
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-badge>

      <el-button
        v-if="!workbench.isAuthenticated.value"
        type="primary"
        :loading="workbench.isLoading.value"
        @click="workbench.beginSignIn"
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
