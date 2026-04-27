<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useLogto } from '@logto/vue'
import { ElMessage } from 'element-plus'

import AnalysisDetailPanel from './components/AnalysisDetailPanel.vue'
import AuthCallbackPanel from './components/AuthCallbackPanel.vue'
import RecordListPanel from './components/RecordListPanel.vue'
import ReportReviewPanel from './components/ReportReviewPanel.vue'
import UnauthorizedPanel from './components/UnauthorizedPanel.vue'
import UploadPanel from './components/UploadPanel.vue'
import { getAuthProfile, getRbacModel } from './api/auth'
import { createAnalysisSocket, getAnalysis, listImages, reviewReport, uploadImage } from './api/analysis'
import { logtoApiResource, setAccessTokenProvider } from './api/http'
import type { AnalysisFilters, AnalysisItem } from './types/analysis'
import type { AuthProfile, MenuCapability, RbacModel } from './types/auth'

type BasicClaims = {
  name?: string
  username?: string
  sub?: string
}

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
const authScopes = ref<string[]>([])
const filters = ref<AnalysisFilters>({
  patient_id: '',
  image_type: '',
  report_status: ''
})

const isCallbackPage = computed(() => window.location.pathname === '/callback')
const currentRecord = computed(() => records.value.find((item: AnalysisItem) => item.image_id === selectedImageId.value) ?? null)
const visibleMenus = computed(() => authProfile.value?.menus.filter((item: MenuCapability) => item.visible) ?? [])
const currentRoles = computed(() => authProfile.value?.roles ?? [])
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
const hasWorkbenchAccess = computed(() => canUpload.value || canReadImages.value || canReview.value)

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
  <div v-else class="page-shell">
    <header class="hero-card">
      <div>
        <p class="eyebrow">Wisdom Tooth AI MVP</p>
        <h1>智齿 AI 医生工作台</h1>
        <p class="hero-desc">覆盖影像上传、AI 初步分析、结果查看、医生审核的最小主链路，并接入 Logto 与 MinIO。</p>
      </div>
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
        <el-tag type="success" size="large">辅助诊断，仅供医生审核参考</el-tag>
        <el-tag v-if="isAuthenticated" type="primary">{{ displayName || '已登录' }}</el-tag>
        <el-tag v-for="role in displayedRoles" :key="role.key" type="warning">{{ role.label }}</el-tag>
        <el-button v-if="!isAuthenticated" type="primary" :loading="isLoading" @click="beginSignIn">使用 Logto 登录</el-button>
        <el-button v-else @click="beginSignOut">退出登录</el-button>
      </div>
    </header>

    <el-alert
      v-if="!isAuthenticated && authReady"
      title="请先登录后再访问影像列表、上传、审核与预览功能"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    />

    <el-alert
      v-else-if="isAuthenticated && authReady"
      :title="`当前角色：${displayedRoles.map((item) => item.label).join(', ') || '未匹配到预设角色'}；当前权限：${authScopes.join(', ') || '无 API scope'}`"
      type="success"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    />

    <div v-if="isAuthenticated && authReady" style="display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap">
      <el-tag v-for="menu in visibleMenus" :key="menu.key" effect="plain">{{ menu.label }}</el-tag>
    </div>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !hasWorkbenchAccess"
      title="当前账号暂无工作台访问权限"
      description="请在 Logto 中为该用户分配 radiologist、doctor 或 chief_doctor 等角色后再重试。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <section v-if="hasWorkbenchAccess" class="grid-layout">
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
    </section>

    <section v-if="hasWorkbenchAccess" class="grid-layout detail-layout">
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
    </section>

    <section v-if="isAuthenticated && authReady && canViewAccessPanel && rbacModel" class="grid-layout detail-layout">
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
        </div>

        <div class="report-box">
          <div class="sub-title">当前权限</div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap">
            <el-tag v-for="permission in authScopes" :key="permission">{{ permission }}</el-tag>
            <span v-if="authScopes.length === 0">无 API 权限</span>
          </div>
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
      </el-card>
    </section>
  </div>
</template>
