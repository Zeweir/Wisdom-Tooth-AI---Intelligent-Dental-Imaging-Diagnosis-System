<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataAnalysis,
  Document,
  Files,
  Fold,
  HomeFilled,
  Operation,
  Setting,
  UploadFilled,
  User,
} from '@element-plus/icons-vue'

import { useWorkbenchContext } from '../workbench'

const props = defineProps<{
  collapsed: boolean
}>()

const emit = defineEmits<{
  toggle: []
}>()

type SidebarItem = {
  key: string
  label: string
  to: string
  icon: typeof HomeFilled
  visible: boolean
}

const route = useRoute()
const workbench = useWorkbenchContext()

const primaryItems = computed<SidebarItem[]>(() => [
  {
    key: 'home',
    label: '工作台',
    to: '/',
    icon: HomeFilled,
    visible: true,
  },
  {
    key: 'patients',
    label: '患者管理',
    to: '/patients',
    icon: User,
    visible: workbench.canReadImages.value,
  },
  {
    key: 'upload',
    label: '影像上传',
    to: '/upload',
    icon: UploadFilled,
    visible: workbench.canUpload.value || workbench.canReadImages.value,
  },
  {
    key: 'diagnosis',
    label: 'AI 诊断',
    to: '/diagnosis',
    icon: DataAnalysis,
    visible: workbench.canReadImages.value,
  },
  {
    key: 'reports',
    label: '诊断报告',
    to: '/reports',
    icon: Document,
    visible: workbench.canReadImages.value,
  },
  {
    key: 'settings',
    label: '系统设置',
    to: '/settings',
    icon: Setting,
    visible: true,
  },
])

const utilityItems = computed<SidebarItem[]>(() => [
  {
    key: 'datasets',
    label: '数据集中心',
    to: '/datasets',
    icon: Files,
    visible: workbench.canReadImages.value,
  },
  {
    key: 'access',
    label: '权限中心',
    to: '/access',
    icon: Operation,
    visible: workbench.canViewAccessPanel.value,
  },
  {
    key: 'audit',
    label: '审计中心',
    to: '/audit',
    icon: Document,
    visible: workbench.canViewAuditLogs.value,
  },
])

function isActive(path: string) {
  return route.path === path
}
</script>

<template>
  <div class="app-sidebar">
    <RouterLink class="app-sidebar-brand" to="/">
      <div class="app-sidebar-logo">智</div>
      <div v-if="!props.collapsed" class="app-sidebar-brand-text">
        <strong>智齿 AI</strong>
        <span>牙齿影像智能诊断系统</span>
      </div>
    </RouterLink>

    <nav class="app-sidebar-nav">
      <RouterLink
        v-for="item in primaryItems.filter((entry) => entry.visible)"
        :key="item.key"
        :to="item.to"
        class="app-sidebar-link"
        :class="{ active: isActive(item.to) }"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span v-if="!props.collapsed">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="app-sidebar-section" v-if="!props.collapsed">更多工具</div>
    <nav class="app-sidebar-nav app-sidebar-nav-sub">
      <RouterLink
        v-for="item in utilityItems.filter((entry) => entry.visible)"
        :key="item.key"
        :to="item.to"
        class="app-sidebar-link"
        :class="{ active: isActive(item.to) }"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span v-if="!props.collapsed">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <button type="button" class="app-sidebar-toggle" @click="emit('toggle')">
      <el-icon :class="{ rotated: props.collapsed }"><Fold /></el-icon>
      <span v-if="!props.collapsed">折叠侧栏</span>
    </button>
  </div>
</template>
