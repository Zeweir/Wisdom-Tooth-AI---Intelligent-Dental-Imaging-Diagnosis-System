<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useLogto } from '@logto/vue'
import { ElMessage } from 'element-plus'

import AnalysisDetailPanel from './components/AnalysisDetailPanel.vue'
import { getAuditLogs } from './api/audit'
import AuthCallbackPanel from './components/AuthCallbackPanel.vue'
import RecordListPanel from './components/RecordListPanel.vue'
import ReportReviewPanel from './components/ReportReviewPanel.vue'
import UnauthorizedPanel from './components/UnauthorizedPanel.vue'
import UploadPanel from './components/UploadPanel.vue'
import { getAuthProfile, getRbacModel } from './api/auth'
import { createAnalysisSocket, getAnalysis, listImages, reviewReport, uploadImage } from './api/analysis'
import { logtoApiResource, setAccessTokenProvider } from './api/http'
import type { AnalysisFilters, AnalysisItem } from './types/analysis'
import type { AuditLogItem } from './types/audit'
import type { AuthProfile, MenuCapability, RbacModel } from './types/auth'

type BasicClaims = {
  name?: string
  username?: string
  sub?: string
}

type SectionKey = 'overview' | 'upload' | 'records' | 'review' | 'access' | 'audit'

const { fetchUserInfo, getAccessToken, getIdTokenClaims, isAuthenticated, isLoading, signIn, signOut } = useLogto()

const loading = ref(false)
const records = ref<AnalysisItem[]>([])
const selectedImageId = ref('')
const reviewText = ref('')
const socketEvents = ref<string[]>([])
const authReady = ref(false)
const displayName = ref('')
const authProfile = ref<AuthProfile | null>(null)
const rbacModel = ref<RbacModel | null>(null)
const auditLogs = ref<AuditLogItem[]>([])
const authScopes = ref<string[]>([])
const activeSection = ref<SectionKey>('overview')
const filters = ref<AnalysisFilters>({
  patient_id: '',
  image_type: '',
  report_status: ''
})

const isCallbackPage = computed(() => window.location.pathname === '/callback')
const currentRecord = computed(() => records.value.find((item: AnalysisItem) => item.image_id === selectedImageId.value) ?? null)
const visibleMenus = computed(() => authProfile.value?.menus.filter((item: MenuCapability) => item.visible) ?? [])
const currentRoles = computed(() => authProfile.value?.roles ?? [])
const tokenRoleLabels = computed(() => authProfile.value?.token_roles ?? [])
const inferredRoleLabels = computed(() => authProfile.value?.inferred_roles ?? [])
const roleSourceLabel = computed(() => {
  if (authProfile.value?.role_source === 'token_claim') {
    return 'Token 角色 Claim'
  }
  if (authProfile.value?.role_source === 'scope_inference') {
    return 'Scope 推断'
  }
  return '未识别'
})
const claimPreviewEntries = computed(() => Object.entries(authProfile.value?.claim_preview ?? {}))
const tokenClaimKeysText = computed(() => authProfile.value?.token_claim_keys.join(', ') || '无')
const roleClaimKeysText = computed(() => authProfile.value?.role_claim_keys.join(', ') || '未命中角色 claim')
const displayedRoles = computed(() => {
  const definitions = rbacModel.value?.roles ?? []
  return currentRoles.value.map((roleKey) => {
    const matched = definitions.find((item) => item.key === roleKey)
    return {
      key: roleKey,
      label: matched?.label ?? roleKey
    }
  })
})
const canUpload = computed(() => visibleMenus.value.some((item: MenuCapability) => item.key === 'upload'))
const canReadImages = computed(() => visibleMenus.value.some((item: MenuCapability) => item.key === 'records'))
const canReview = computed(() => visibleMenus.value.some((item: MenuCapability) => item.key === 'review'))
const canFinalize = computed(() => authScopes.value.includes('finalize:reports'))
const canViewAccessPanel = computed(() => visibleMenus.value.some((item: MenuCapability) => item.key === 'access'))
const canViewAuditLogs = computed(() => visibleMenus.value.some((item: MenuCapability) => item.key === 'audit'))
const hasWorkbenchAccess = computed(() => canUpload.value || canReadImages.value || canReview.value)
const configuredRoleClaimNamesText = computed(() => authProfile.value?.configured_role_claim_names.join(', ') || '未配置')
const roleClaimAlignmentTagType = computed(() => {
  if (authProfile.value?.role_claim_alignment_status === 'aligned') {
    return 'success'
  }
  if (authProfile.value?.role_claim_alignment_status === 'fallback_scope_inference') {
    return 'warning'
  }
  return 'danger'
})
const roleClaimAlignmentLabel = computed(() => {
  if (authProfile.value?.role_claim_alignment_status === 'aligned') {
    return '已通过 Token Claim 对齐'
  }
  if (authProfile.value?.role_claim_alignment_status === 'claim_required_missing') {
    return '已开启严格模式，但 Token 未携带角色 Claim'
  }
  if (authProfile.value?.role_claim_alignment_status === 'fallback_scope_inference') {
    return '当前仍在使用 Scope 推断'
  }
  return '未识别到角色 Claim'
})
const navigationItems = computed(() => {
  const items: Array<{ key: SectionKey; label: string; caption: string }> = [
    { key: 'overview', label: '总览', caption: '工作台概况' }
  ]

  if (canUpload.value) {
    items.push({ key: 'upload', label: '影像接入', caption: '上传与分析' })
  }
  if (canReadImages.value) {
    items.push({ key: 'records', label: '分析记录', caption: '列表与筛选' })
  }
  if (canReadImages.value || canReview.value) {
    items.push({ key: 'review', label: '报告中心', caption: '结果与审核' })
  }
  if (canViewAccessPanel.value) {
    items.push({ key: 'access', label: '权限模型', caption: '角色与 RBAC' })
  }
  if (canViewAuditLogs.value) {
    items.push({ key: 'audit', label: '审计日志', caption: '关键留痕' })
  }

  return items
})
const dashboardStats = computed(() => [
  {
    label: '可见菜单',
    value: visibleMenus.value.length,
    description: '当前账号可访问的工作台模块数'
  },
  {
    label: '影像记录',
    value: records.value.length,
    description: '当前筛选条件下可查看的病例记录'
  },
  {
    label: '当前病灶数',
    value: currentRecord.value?.detections.length ?? 0,
    description: '当前选中记录中的检测结果数量'
  },
  {
    label: '审计事件',
    value: auditLogs.value.length,
    description: '最近一次读取到的关键留痕数量'
  }
])

async function refreshAuditLogs() {
  if (!canViewAuditLogs.value) {
    auditLogs.value = []
    return
  }
  try {
    auditLogs.value = await getAuditLogs({ limit: 20 })
  } catch {
    auditLogs.value = []
  }
}

function focusSection(section: SectionKey) {
  activeSection.value = section
  const targetSection = section === 'records' ? 'upload' : section
  const element = document.getElementById(`section-${targetSection}`)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function normalizeAccessToken(token: string | undefined | null) {
  return token ?? null
}

async function refreshAuthState() {
  if (!isAuthenticated.value) {
    authProfile.value = null
    rbacModel.value = null
    auditLogs.value = []
    displayName.value = ''
    authScopes.value = []
    authReady.value = true
    return
  }

  const [claims, userInfo, profile, model] = await Promise.all([
    getIdTokenClaims() as Promise<BasicClaims | undefined>,
    fetchUserInfo().catch(() => null),
    getAuthProfile(),
    getRbacModel()
  ])

  displayName.value = String(
    userInfo?.name ?? claims?.name ?? claims?.username ?? claims?.sub ?? '已登录用户'
  )
  authProfile.value = profile
  rbacModel.value = model
  authScopes.value = profile.permissions
  if (profile.menus.some((item: MenuCapability) => item.key === 'audit' && item.visible)) {
    await refreshAuditLogs()
  } else {
    auditLogs.value = []
  }
  authReady.value = true
}

async function beginSignIn() {
  await signIn(`${window.location.origin}/callback`)
}

async function beginSignOut() {
  await signOut(window.location.origin)
}

async function fetchRecords() {
  if (!canReadImages.value) {
    records.value = []
    selectedImageId.value = ''
    reviewText.value = ''
    return
  }
  records.value = await listImages(filters.value)
  if (selectedImageId.value && !records.value.some((item: AnalysisItem) => item.image_id === selectedImageId.value)) {
    selectedImageId.value = ''
    reviewText.value = ''
  }
  if (!selectedImageId.value && records.value.length > 0) {
    selectedImageId.value = records.value[0].image_id
  }
}

async function fetchAnalysisRecord(imageId: string) {
  if (!canReadImages.value) {
    return
  }
  const current = await getAnalysis(imageId)
  const index = records.value.findIndex((item: AnalysisItem) => item.image_id === imageId)
  if (index >= 0) {
    records.value[index] = current
  } else {
    records.value.unshift(current)
  }
  selectedImageId.value = imageId
  reviewText.value = current.report.doctor_review ?? ''
}

async function waitForAnalysisCompletion(imageId: string) {
  if (!canReadImages.value) {
    return null
  }
  for (let attempt = 0; attempt < 10; attempt += 1) {
    const current = await getAnalysis(imageId)
    const index = records.value.findIndex((item: AnalysisItem) => item.image_id === imageId)
    if (index >= 0) {
      records.value[index] = current
    } else {
      records.value.unshift(current)
    }
    selectedImageId.value = imageId
    reviewText.value = current.report.doctor_review ?? ''
    if (current.status !== 'processing') {
      return current
    }
    await sleep(800)
  }
  return null
}

async function handleUpload(payload: { file: File; patientId: string; imageType: AnalysisItem['image_type'] }) {
  if (!canUpload.value) {
    ElMessage.warning('你当前没有上传影像的权限')
    return
  }
  loading.value = true
  try {
    const result = await uploadImage(payload)
    ElMessage.success('上传成功')
    connectProgress(result.image_id)
    const completed = await waitForAnalysisCompletion(result.image_id)
    if (!completed) {
      ElMessage.warning('分析仍在处理中，请稍后刷新查看结果')
    }
    await fetchRecords()
    await refreshAuditLogs()
  } finally {
    loading.value = false
  }
}

async function applyFilters() {
  if (!canReadImages.value) {
    return
  }
  await fetchRecords()
  if (selectedImageId.value) {
    await fetchAnalysisRecord(selectedImageId.value)
  }
}

async function resetFilters() {
  filters.value = {
    patient_id: '',
    image_type: '',
    report_status: ''
  }
  await applyFilters()
}

async function handleReviewSubmit() {
  if (!canReview.value) {
    ElMessage.warning('你当前没有审核报告的权限')
    return
  }
  if (!currentRecord.value) {
    ElMessage.warning('请先选择分析记录')
    return
  }

  await reviewReport(currentRecord.value.report.report_id, {
    doctor_review: reviewText.value,
    modified_findings: currentRecord.value.detections,
    status: 'doctor_reviewed'
  })
  ElMessage.success('审核意见已提交')
  await fetchAnalysisRecord(currentRecord.value.image_id)
  await refreshAuditLogs()
}

async function handleFinalizeSubmit() {
  if (!canFinalize.value) {
    ElMessage.warning('你当前没有正式确认报告的权限')
    return
  }
  if (!currentRecord.value) {
    ElMessage.warning('请先选择分析记录')
    return
  }

  await reviewReport(currentRecord.value.report.report_id, {
    doctor_review: reviewText.value,
    modified_findings: currentRecord.value.detections,
    status: 'finalized'
  })
  ElMessage.success('报告已正式确认')
  await fetchAnalysisRecord(currentRecord.value.image_id)
  await fetchRecords()
  await refreshAuditLogs()
}

function connectProgress(imageId: string) {
  socketEvents.value = []
  getAccessToken(logtoApiResource).then((rawAccessToken) => {
    const accessToken = normalizeAccessToken(rawAccessToken)
    if (!accessToken) {
      socketEvents.value.push('analysis.socket_error / missing_token')
      return
    }
    const socket = createAnalysisSocket(imageId, accessToken)
    socket.onmessage = (event: MessageEvent<string>) => {
      const payload = JSON.parse(event.data) as { event: string; status: string }
      socketEvents.value.push(`${payload.event} / ${payload.status}`)
    }
    socket.onerror = () => {
      socketEvents.value.push('analysis.socket_error / unavailable')
    }
  })
}

watch(isAuthenticated, async () => {
  await refreshAuthState()
  if (!isAuthenticated.value) {
    records.value = []
    selectedImageId.value = ''
    reviewText.value = ''
    return
  }
  if (!isCallbackPage.value) {
    await fetchRecords()
    if (selectedImageId.value) {
      await fetchAnalysisRecord(selectedImageId.value)
    }
  }
})

onMounted(async () => {
  setAccessTokenProvider(async () => {
    if (!isAuthenticated.value) {
      return null
    }
    return normalizeAccessToken(await getAccessToken(logtoApiResource))
  })
  await refreshAuthState()
  if (isAuthenticated.value && !isCallbackPage.value) {
    await fetchRecords()
    if (selectedImageId.value) {
      await fetchAnalysisRecord(selectedImageId.value)
    }
  }
})
</script>

<template>
  <AuthCallbackPanel v-if="isCallbackPage" />
  <div v-else class="dashboard-shell">
    <div class="dashboard-backdrop" />
    <div class="page-shell dashboard-frame">
      <header class="topbar-card">
        <div class="brand-block">
          <div class="brand-icon">WT</div>
          <div>
            <p class="eyebrow">Wisdom Tooth AI Platform</p>
            <h1>智齿 AI 医生工作台</h1>
            <p class="hero-desc">围绕影像上传、AI 分析、医生审核和权限留痕构建的一体化牙科影像工作台。</p>
          </div>
        </div>
        <div class="topbar-actions">
          <el-tag type="success" size="large">辅助诊断，仅供医生审核参考</el-tag>
          <el-tag v-if="isAuthenticated" type="primary">{{ displayName || '已登录' }}</el-tag>
          <el-tag v-for="role in displayedRoles" :key="role.key" type="warning">{{ role.label }}</el-tag>
          <el-button v-if="!isAuthenticated" type="primary" :loading="isLoading" @click="beginSignIn">使用 Logto 登录</el-button>
          <el-button v-else @click="beginSignOut">退出登录</el-button>
        </div>
      </header>

      <div class="workspace-layout">
        <aside class="sidebar-card">
          <div class="sidebar-section">
            <div class="sidebar-title">工作台导航</div>
            <button
              v-for="item in navigationItems"
              :key="item.key"
              class="nav-item"
              :class="{ active: activeSection === item.key }"
              @click="focusSection(item.key)"
            >
              <span class="nav-label">{{ item.label }}</span>
              <span class="nav-caption">{{ item.caption }}</span>
            </button>
          </div>

          <div class="sidebar-section sidebar-summary">
            <div class="sidebar-title">当前访问</div>
            <div class="sidebar-user">{{ isAuthenticated ? (displayName || '已登录用户') : '未登录' }}</div>
            <div class="sidebar-tags">
              <el-tag v-for="menu in visibleMenus" :key="menu.key" effect="plain">{{ menu.label }}</el-tag>
            </div>
            <div class="sidebar-hint">
              {{ isAuthenticated ? `权限数：${authScopes.length} / 角色数：${displayedRoles.length}` : '登录后可查看工作台模块与权限摘要' }}
            </div>
          </div>
        </aside>

        <main class="content-stack">
          <section id="section-overview" class="overview-hero">
            <div class="overview-copy">
              <div class="overview-pill">智能影像诊断工作流</div>
              <h2>用更清晰的分区管理上传、分析、审核和权限</h2>
              <p>
                你现在看到的是升级后的工作台骨架：左侧负责导航，右侧负责内容流，重点信息会优先展示在总览和关键面板里。
              </p>
            </div>
            <div class="stats-grid">
              <div v-for="stat in dashboardStats" :key="stat.label" class="stat-card">
                <div class="stat-value">{{ stat.value }}</div>
                <div class="stat-label">{{ stat.label }}</div>
                <div class="stat-desc">{{ stat.description }}</div>
              </div>
            </div>
          </section>

          <el-alert
            v-if="!isAuthenticated && authReady"
            title="请先登录后再访问影像列表、上传、审核与预览功能"
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

          <UnauthorizedPanel
            v-if="isAuthenticated && authReady && !hasWorkbenchAccess"
            title="当前账号暂无工作台访问权限"
            description="请在 Logto 中为该用户分配 radiologist、doctor 或 chief_doctor 等角色后再重试。"
          >
            <el-button @click="beginSignOut">退出当前账号</el-button>
          </UnauthorizedPanel>

          <template v-if="hasWorkbenchAccess">
            <section id="section-upload" class="section-block">
              <div class="section-heading">
                <div>
                  <h3>影像接入区</h3>
                  <p>从患者影像上传开始，进入 AI 分析和实时事件追踪。</p>
                </div>
                <el-button v-if="canUpload" text @click="focusSection('records')">查看最新记录</el-button>
              </div>

              <div class="grid-layout">
                <UploadPanel
                  v-if="canUpload"
                  v-model:loading="loading"
                  v-model:socket-events="socketEvents"
                  :can-upload="canUpload"
                  @submit="handleUpload"
                />

                <UnauthorizedPanel
                  v-else
                  title="当前角色不可上传影像"
                  description="上传影像需要 `upload:images` 权限，请为当前用户分配 radiologist 或包含该权限的角色。"
                />

                <RecordListPanel
                  v-if="canReadImages"
                  :filters="filters"
                  :records="records"
                  :selected-image-id="selectedImageId"
                  @refresh="fetchRecords"
                  @apply-filters="applyFilters"
                  @reset-filters="resetFilters"
                  @select="fetchAnalysisRecord"
                />

                <UnauthorizedPanel
                  v-else
                  title="当前角色不可查看分析记录"
                  description="查看影像、详情和预览需要 `read:images` 权限。"
                />
              </div>
            </section>

            <section id="section-review" class="section-block">
              <div class="section-heading">
                <div>
                  <h3>分析与审核中心</h3>
                  <p>查看当前选中病例的影像预览、检测结果、AI 报告和医生审核意见。</p>
                </div>
                <div class="section-heading-tags">
                  <el-tag v-if="currentRecord" type="info">当前病例：{{ currentRecord.patient_id }}</el-tag>
                  <el-tag v-if="currentRecord" type="success">{{ currentRecord.report.status }}</el-tag>
                </div>
              </div>

              <div class="grid-layout detail-layout">
                <AnalysisDetailPanel v-if="canReadImages" :current-record="currentRecord" />

                <UnauthorizedPanel
                  v-else
                  title="当前角色不可查看影像详情"
                  description="如需浏览检测结果和影像预览，请为用户分配 `read:images` 权限。"
                />

                <ReportReviewPanel
                  v-if="canReview || canReadImages"
                  v-model:review-text="reviewText"
                  :current-record="currentRecord"
                  :can-review="canReview"
                  :can-finalize-report="canFinalize"
                  @submit="handleReviewSubmit"
                  @finalize="handleFinalizeSubmit"
                />

                <UnauthorizedPanel
                  v-else
                  title="当前角色不可审核报告"
                  description="提交审核意见需要 `review:reports` 权限，正式确认还需要 `finalize:reports` 权限。"
                />
              </div>
            </section>

            <section id="section-access" v-if="isAuthenticated && authReady && canViewAccessPanel && rbacModel" class="section-block">
              <div class="section-heading">
                <div>
                  <h3>权限模型与访问画像</h3>
                  <p>集中查看当前登录用户的角色来源、权限范围、菜单可见性和系统 RBAC 配置。</p>
                </div>
              </div>

              <div class="grid-layout detail-layout">
                <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>当前访问画像</span>
            <span>{{ authProfile?.sub }}</span>
          </div>
        </template>

        <div class="report-box">
          <div class="sub-title">当前角色</div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap">
            <el-tag v-for="role in displayedRoles" :key="role.key" type="warning">{{ role.label }}</el-tag>
            <span v-if="currentRoles.length === 0">未匹配到预设角色</span>
          </div>
          <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center">
            <el-tag type="info">角色来源：{{ roleSourceLabel }}</el-tag>
            <el-tag effect="plain">Token Claim Keys：{{ roleClaimKeysText }}</el-tag>
            <el-tag :type="roleClaimAlignmentTagType">{{ roleClaimAlignmentLabel }}</el-tag>
          </div>
        </div>

        <div class="report-box">
          <div class="sub-title">当前权限</div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap">
            <el-tag v-for="permission in authScopes" :key="permission">{{ permission }}</el-tag>
            <span v-if="authScopes.length === 0">无 API 权限</span>
          </div>
        </div>

        <div class="report-box">
          <div class="sub-title">角色解析调试</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="Token 角色">
              {{ tokenRoleLabels.join(', ') || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="Scope 推断角色">
              {{ inferredRoleLabels.join(', ') || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="最终采用角色">
              {{ displayedRoles.map((item) => item.label).join(', ') || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="Token Claim Keys">
              {{ tokenClaimKeysText }}
            </el-descriptions-item>
            <el-descriptions-item label="期望角色 Claim 名">
              {{ configuredRoleClaimNamesText }}
            </el-descriptions-item>
            <el-descriptions-item label="严格 Claim 模式">
              {{ authProfile?.role_claim_required ? '已开启' : '未开启' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="report-box">
          <div class="sub-title">Claim 摘要</div>
          <el-table :data="claimPreviewEntries.map(([key, value]) => ({ key, value }))" stripe>
            <el-table-column prop="key" label="Claim" min-width="180" />
            <el-table-column label="Value" min-width="260">
              <template #default="scope">
                {{ typeof scope.row.value === 'string' ? scope.row.value : JSON.stringify(scope.row.value) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="report-box">
          <div class="sub-title">可见菜单</div>
          <el-table :data="visibleMenus" stripe>
            <el-table-column prop="label" label="菜单" min-width="120" />
            <el-table-column prop="description" label="说明" min-width="220" />
            <el-table-column label="所需权限" min-width="180">
              <template #default="scope">
                {{ scope.row.required_scopes.join(', ') || '无' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

                <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>系统 RBAC 模型</span>
            <span>{{ rbacModel.resource }}</span>
          </div>
        </template>

        <div class="report-box">
          <div class="sub-title">角色定义</div>
          <el-table :data="rbacModel.roles" stripe>
            <el-table-column prop="label" label="角色" min-width="120" />
            <el-table-column prop="key" label="Key" min-width="140" />
            <el-table-column prop="description" label="说明" min-width="220" />
            <el-table-column label="权限" min-width="220">
              <template #default="scope">
                {{ scope.row.scopes.join(', ') }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="report-box">
          <div class="sub-title">权限定义</div>
          <el-table :data="rbacModel.permissions" stripe>
            <el-table-column prop="label" label="权限" min-width="120" />
            <el-table-column prop="key" label="Key" min-width="160" />
            <el-table-column prop="description" label="说明" min-width="240" />
          </el-table>
        </div>

        <div class="report-box">
          <div class="sub-title">角色解析规则</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="优先来源">
              {{ rbacModel.role_resolution.preferred_source }}
            </el-descriptions-item>
            <el-descriptions-item label="兜底来源">
              {{ rbacModel.role_resolution.fallback_source }}
            </el-descriptions-item>
            <el-descriptions-item label="候选 Claim">
              {{ rbacModel.role_resolution.token_role_claim_candidates.join(', ') }}
            </el-descriptions-item>
            <el-descriptions-item label="说明">
              {{ rbacModel.role_resolution.description }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="report-box">
          <div class="sub-title">Logto Role Claim 配置</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="配置 Claim 名">
              {{ rbacModel.logto_claim_setup.configured_claim_names.join(', ') }}
            </el-descriptions-item>
            <el-descriptions-item label="函数名">
              {{ rbacModel.logto_claim_setup.custom_jwt_function_name }}
            </el-descriptions-item>
            <el-descriptions-item label="函数签名">
              {{ rbacModel.logto_claim_setup.custom_jwt_function_signature }}
            </el-descriptions-item>
            <el-descriptions-item label="严格模式">
              {{ rbacModel.logto_claim_setup.role_claim_required ? '开启' : '关闭' }}
            </el-descriptions-item>
          </el-descriptions>
          <el-input
            :model-value="rbacModel.logto_claim_setup.recommended_script"
            type="textarea"
            :rows="8"
            readonly
            style="margin-top: 12px"
          />
        </div>
      </el-card>
              </div>
            </section>

            <section id="section-audit" v-if="isAuthenticated && authReady && canViewAuditLogs" class="section-block">
              <div class="section-heading">
                <div>
                  <h3>审计日志</h3>
                  <p>查看上传、审核、确认和后台分析完成等关键操作留痕。</p>
                </div>
                <el-button text @click="refreshAuditLogs">刷新日志</el-button>
              </div>

              <div class="grid-layout detail-layout">
                <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>关键审计日志</span>
            <el-button text @click="refreshAuditLogs">刷新</el-button>
          </div>
        </template>

        <el-table :data="auditLogs" stripe>
          <el-table-column prop="created_at" label="时间" min-width="180" />
          <el-table-column prop="action" label="动作" min-width="160" />
          <el-table-column prop="resource_type" label="资源类型" min-width="120" />
          <el-table-column prop="resource_id" label="资源 ID" min-width="180" />
          <el-table-column prop="actor_sub" label="操作者" min-width="220" />
          <el-table-column label="详情" min-width="280">
            <template #default="scope">
              {{ JSON.stringify(scope.row.detail) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
              </div>
            </section>
          </template>
        </main>
      </div>
    </div>
  </div>
</template>
