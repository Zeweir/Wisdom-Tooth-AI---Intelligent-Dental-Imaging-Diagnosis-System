<script setup lang="ts">
import { computed } from 'vue'

import EmptyState from '../components/EmptyState.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()

const toolEntries = computed(() => [
  {
    key: 'datasets',
    title: '数据集中心',
    description: '管理公开数据集来源、导入批次和模型评估记录。',
    to: '/datasets',
    visible: workbench.canReadImages.value,
  },
  {
    key: 'access',
    title: '权限中心',
    description: '查看当前账号角色、可访问菜单与权限能力。',
    to: '/access',
    visible: workbench.canViewAccessPanel.value,
  },
  {
    key: 'audit',
    title: '审计中心',
    description: '追踪影像上传、报告审核、模型评估等关键操作日志。',
    to: '/audit',
    visible: workbench.canViewAuditLogs.value,
  },
].filter((item) => item.visible))
</script>

<template>
  <div class="page-stack">
    <PageHeader
      title="系统设置"
      description="医疗核心流程以外的系统能力统一收纳在此，避免占用主导航。"
    />

    <el-card class="panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <span>账号信息</span>
          <el-tag type="info">{{ workbench.displayName.value || '未登录' }}</el-tag>
        </div>
      </template>
      <div class="settings-role-list">
        <el-tag
          v-for="role in workbench.displayedRoles.value"
          :key="role.key"
          type="warning"
          effect="light"
        >
          {{ role.label }}
        </el-tag>
        <el-tag v-if="workbench.displayedRoles.value.length === 0" type="info" effect="light">暂无角色</el-tag>
      </div>
    </el-card>

    <EmptyState
      v-if="toolEntries.length === 0"
      title="暂无可用系统工具"
      description="当前角色未开通数据集、权限或审计中心访问能力。"
    />

    <section v-else class="settings-grid">
      <el-card
        v-for="item in toolEntries"
        :key="item.key"
        class="panel settings-entry-card"
        shadow="never"
      >
        <h3>{{ item.title }}</h3>
        <p>{{ item.description }}</p>
        <RouterLink :to="item.to" class="el-button el-button--primary is-plain">
          <span>进入</span>
        </RouterLink>
      </el-card>
    </section>
  </div>
</template>
