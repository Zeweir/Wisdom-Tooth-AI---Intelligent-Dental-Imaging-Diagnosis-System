<script setup lang="ts">
import { computed } from 'vue'

import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import { getScopeLabel } from '../utils/display'
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()
const canViewAccessPanel = workbench.canViewAccessPanel
const rbacModel = workbench.rbacModel
const displayedRoles = workbench.displayedRoles
const currentRoles = workbench.currentRoles
const authScopes = workbench.authScopes
const visibleMenus = workbench.visibleMenus
const currentActionLabels = computed(() => authScopes.value.map((scope) => getScopeLabel(scope)))
const roleSummaryText = computed(() => displayedRoles.value.map((item) => item.label).join('、') || '未匹配到预设角色')
const visibleMenuLabels = computed(() => visibleMenus.value.map((item) => item.label))
const roleDescriptions = computed(() => {
  if (!rbacModel.value) {
    return []
  }
  return displayedRoles.value.map((role) => {
    const matched = rbacModel.value?.roles.find((item) => item.key === role.key)
    return {
      label: role.label,
      description: matched?.description ?? '当前角色已具备对应临床操作权限。',
      scopes: (matched?.scopes ?? []).map((scope) => getScopeLabel(scope))
    }
  })
})
const allRoleCards = computed(() => rbacModel.value?.roles.map((role) => ({
  ...role,
  scopeLabels: role.scopes.map((scope) => getScopeLabel(scope)),
  active: currentRoles.value.includes(role.key)
})) ?? [])
</script>

<template>
  <div class="page-stack">
    <section class="medical-page-header">
      <div>
        <div class="overview-pill">权限中心</div>
        <h2>当前账号可执行哪些临床操作</h2>
        <p>这里只保留医生真正关心的角色、可用功能和可执行动作，不再展示底层调试参数。</p>
      </div>
    </section>

    <UnauthorizedPanel
      v-if="!canViewAccessPanel"
      title="当前角色不可查看权限中心"
      description="如需查看当前访问画像和 RBAC 模型，请为当前用户分配 access 菜单对应权限。"
    />

    <div v-else-if="rbacModel" class="grid-layout detail-layout">
      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>当前账号职责</span>
            <el-tag type="info">医生可见摘要</el-tag>
          </div>
        </template>

        <div class="report-box">
          <div class="sub-title">当前角色</div>
          <div class="tag-wrap">
            <el-tag v-for="role in displayedRoles" :key="role.key" type="warning">{{ role.label }}</el-tag>
            <span v-if="currentRoles.length === 0">未匹配到预设角色</span>
          </div>
          <p class="clinical-copy">{{ roleSummaryText }}</p>
        </div>

        <div class="report-box">
          <div class="sub-title">当前可执行动作</div>
          <div class="tag-wrap">
            <el-tag v-for="permission in currentActionLabels" :key="permission">{{ permission }}</el-tag>
            <span v-if="authScopes.length === 0">无 API 权限</span>
          </div>
        </div>

        <div class="report-box">
          <div class="sub-title">可进入的工作区</div>
          <div class="tag-wrap">
            <el-tag v-for="menu in visibleMenuLabels" :key="menu" effect="plain">{{ menu }}</el-tag>
            <span v-if="visibleMenuLabels.length === 0">暂无可进入模块</span>
          </div>
        </div>
      </el-card>

      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>角色职责说明</span>
            <el-tag type="success">临床视角</el-tag>
          </div>
        </template>

        <div class="report-box">
          <div class="role-summary-list">
            <div v-for="role in roleDescriptions" :key="role.label" class="role-summary-item">
              <div class="role-summary-header">
                <strong>{{ role.label }}</strong>
              </div>
              <p>{{ role.description }}</p>
              <div class="tag-wrap">
                <el-tag v-for="scope in role.scopes" :key="scope" effect="plain">{{ scope }}</el-tag>
              </div>
            </div>
          </div>

          <div v-if="roleDescriptions.length === 0" class="clinical-copy">当前账号还未匹配到明确的角色职责说明。</div>
        </div>
      </el-card>
    </div>

    <section v-if="canViewAccessPanel && rbacModel" class="section-block">
      <div class="section-heading">
        <div>
          <h3>系统角色矩阵</h3>
          <p>用临床职责视角展示每个角色能进入哪些关键操作，当前账号角色会被高亮。</p>
        </div>
      </div>

      <div class="feature-grid">
        <el-card v-for="role in allRoleCards" :key="role.key" class="panel feature-card" shadow="never">
          <div class="panel-header">
            <span>{{ role.label }}</span>
            <el-tag :type="role.active ? 'success' : 'info'">{{ role.active ? '当前账号' : '可配置角色' }}</el-tag>
          </div>
          <p class="clinical-copy">{{ role.description }}</p>
          <div class="tag-wrap tag-wrap-top">
            <el-tag v-for="scope in role.scopeLabels" :key="scope" effect="plain">{{ scope }}</el-tag>
          </div>
        </el-card>
      </div>
    </section>
  </div>
</template>
