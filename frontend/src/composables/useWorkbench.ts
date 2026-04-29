import { computed, onMounted, ref, watch } from 'vue'
import { useLogto } from '@logto/vue'
import { ElMessage } from 'element-plus'

import { getAuditLogs } from '../api/audit'
import { getAuthProfile, getRbacModel } from '../api/auth'
import { createAnalysisSocket, getAnalysis, getDashboardSummary, listImages, reviewReport, uploadImage } from '../api/analysis'
import { logtoApiResource, setAccessTokenProvider } from '../api/http'
import type { AnalysisFilters, AnalysisItem, DashboardSummary, PaginationMeta } from '../types/analysis'
import type { AuditLogFilters, AuditLogItem, AuditLogPagination } from '../types/audit'
import type { AuthProfile, MenuCapability, RbacModel } from '../types/auth'
import type { WorkbenchContext } from '../workbench'

type BasicClaims = {
  name?: string
  username?: string
  sub?: string
}

export function useWorkbench(): WorkbenchContext {
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
  const auditFilters = ref<AuditLogFilters>({
    action: '',
    resource_type: '',
    resource_id: '',
    actor_sub: ''
  })
  const auditPagination = ref<AuditLogPagination>({
    limit: 10,
    offset: 0,
    total: 0
  })
  const authScopes = ref<string[]>([])
  const dashboardSummary = ref<DashboardSummary | null>(null)
  const recordsPagination = ref<PaginationMeta>({
    limit: 10,
    offset: 0,
    total: 0
  })
  const filters = ref<AnalysisFilters>({
    patient_id: '',
    image_type: '',
    report_status: ''
  })

  const currentRecord = computed(() => records.value.find((item) => item.image_id === selectedImageId.value) ?? null)
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
  const canUpload = computed(() => visibleMenus.value.some((item) => item.key === 'upload'))
  const canReadImages = computed(() => visibleMenus.value.some((item) => item.key === 'records'))
  const canReview = computed(() => visibleMenus.value.some((item) => item.key === 'review'))
  const canFinalize = computed(() => authScopes.value.includes('finalize:reports'))
  const canViewAccessPanel = computed(() => visibleMenus.value.some((item) => item.key === 'access'))
  const canViewAuditLogs = computed(() => visibleMenus.value.some((item) => item.key === 'audit'))
  const hasWorkbenchAccess = computed(() => canUpload.value || canReadImages.value || canReview.value)
  const configuredRoleClaimNamesText = computed(() => authProfile.value?.configured_role_claim_names.join(', ') || '未配置')
  const roleClaimAlignmentTagType = computed(() => {
    if (authProfile.value?.role_claim_alignment_status === 'aligned') {
      return 'success' as const
    }
    if (authProfile.value?.role_claim_alignment_status === 'fallback_scope_inference') {
      return 'warning' as const
    }
    return 'danger' as const
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
    const items: WorkbenchContext['navigationItems']['value'] = [
      { key: 'home', label: '临床总览', caption: '首页与工作台总览', shortLabel: '首页', to: '/' },
      { key: 'workspace', label: '影像工作站', caption: '上传、记录、分析与审核', shortLabel: '工作站', to: '/workspace' }
    ]

    if (canReadImages.value) {
      items.push({ key: 'patients', label: '患者档案', caption: '患者列表、病例统计与历史影像', shortLabel: '患者', to: '/patients' })
      items.push({ key: 'datasets', label: '数据集中心', caption: '公开数据集、许可与适用任务', shortLabel: '数据集', to: '/datasets' })
    }
    if (canViewAccessPanel.value) {
      items.push({ key: 'access', label: '权限与角色', caption: 'RBAC 与访问画像', shortLabel: '权限', to: '/access' })
    }
    if (canViewAuditLogs.value) {
      items.push({ key: 'audit', label: '审计中心', caption: '关键留痕与事件追踪', shortLabel: '审计', to: '/audit' })
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
  const clinicalInsights = computed(() => {
    const fallbackDetections = records.value.flatMap((item) => item.detections)
    if (!dashboardSummary.value) {
      const averageConfidence = fallbackDetections.length
        ? Math.round(
            (fallbackDetections.reduce((sum, item) => sum + item.confidence, 0) / fallbackDetections.length) * 100
          )
        : 0
      return [
        {
          label: '正式报告',
          value: records.value.filter((item) => item.report.status === 'finalized').length,
          description: '已由医生确认的报告数量'
        },
        {
          label: '平均置信度',
          value: averageConfidence,
          description: '当前病例列表内 AI 检测平均置信度'
        },
        {
          label: '处理中',
          value: records.value.filter((item) => item.status === 'processing').length,
          description: '仍在等待 AI 分析完成的影像'
        }
      ]
    }

    return [
      {
        label: '患者档案',
        value: dashboardSummary.value.total_patients,
        description: `近 7 天新增 ${dashboardSummary.value.recent_patients} 位患者`
      },
      {
        label: '公开数据集',
        value: dashboardSummary.value.dataset_count,
        description: `开放可访问 ${dashboardSummary.value.open_dataset_count} 个，覆盖 ${dashboardSummary.value.covered_disease_count} 类标签`
      },
      {
        label: '处理中',
        value: dashboardSummary.value.processing_images,
        description: '仍处于 AI 分析中的影像记录'
      }
    ]
  })

  async function refreshAuditLogs() {
    if (!canViewAuditLogs.value) {
      auditLogs.value = []
      auditPagination.value = { ...auditPagination.value, offset: 0, total: 0 }
      return
    }
    try {
      const result = await getAuditLogs({
        limit: auditPagination.value.limit,
        offset: auditPagination.value.offset,
        ...auditFilters.value
      })
      auditLogs.value = result.items
      auditPagination.value = result.meta
    } catch {
      auditLogs.value = []
      auditPagination.value = { ...auditPagination.value, total: 0 }
    }
  }

  async function refreshDashboardSummary() {
    if (!canReadImages.value) {
      dashboardSummary.value = null
      return
    }
    try {
      dashboardSummary.value = await getDashboardSummary()
    } catch {
      dashboardSummary.value = null
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
      dashboardSummary.value = null
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
    await refreshDashboardSummary()
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
      recordsPagination.value = { ...recordsPagination.value, offset: 0, total: 0 }
      return
    }
    const result = await listImages(filters.value, {
      limit: recordsPagination.value.limit,
      offset: recordsPagination.value.offset
    })
    records.value = result.items
    recordsPagination.value = result.meta
    if (selectedImageId.value && !records.value.some((item) => item.image_id === selectedImageId.value)) {
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
    const index = records.value.findIndex((item) => item.image_id === imageId)
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
      const index = records.value.findIndex((item) => item.image_id === imageId)
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

  async function handleUpload(payload: { file: File; patientId: string; patientName?: string; imageType: AnalysisItem['image_type'] }) {
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
      await refreshDashboardSummary()
      await refreshAuditLogs()
    } finally {
      loading.value = false
    }
  }

  async function applyFilters() {
    if (!canReadImages.value) {
      return
    }
    recordsPagination.value = { ...recordsPagination.value, offset: 0 }
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

  async function handleRecordsPageChange(page: number) {
    recordsPagination.value = {
      ...recordsPagination.value,
      offset: (page - 1) * recordsPagination.value.limit
    }
    await fetchRecords()
  }

  async function handleRecordsPageSizeChange(pageSize: number) {
    recordsPagination.value = {
      ...recordsPagination.value,
      limit: pageSize,
      offset: 0
    }
    await fetchRecords()
  }

  async function applyAuditFilters() {
    auditPagination.value = {
      ...auditPagination.value,
      offset: 0
    }
    await refreshAuditLogs()
  }

  async function resetAuditFilters() {
    auditFilters.value = {
      action: '',
      resource_type: '',
      resource_id: '',
      actor_sub: ''
    }
    await applyAuditFilters()
  }

  async function handleAuditPageChange(page: number) {
    auditPagination.value = {
      ...auditPagination.value,
      offset: (page - 1) * auditPagination.value.limit
    }
    await refreshAuditLogs()
  }

  async function handleAuditPageSizeChange(pageSize: number) {
    auditPagination.value = {
      ...auditPagination.value,
      limit: pageSize,
      offset: 0
    }
    await refreshAuditLogs()
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
    await refreshDashboardSummary()
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
    await refreshDashboardSummary()
  }

  watch(isAuthenticated, async () => {
    await refreshAuthState()
    if (!isAuthenticated.value) {
      records.value = []
      selectedImageId.value = ''
      reviewText.value = ''
      dashboardSummary.value = null
      return
    }
    await fetchRecords()
    await refreshDashboardSummary()
    if (selectedImageId.value) {
      await fetchAnalysisRecord(selectedImageId.value)
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
    if (isAuthenticated.value) {
      await fetchRecords()
      await refreshDashboardSummary()
      if (selectedImageId.value) {
        await fetchAnalysisRecord(selectedImageId.value)
      }
    }
  })

  return {
    loading,
    records,
    selectedImageId,
    reviewText,
    socketEvents,
    authReady,
    displayName,
    authProfile,
    rbacModel,
    auditLogs,
    auditFilters,
    auditPagination,
    authScopes,
    dashboardSummary,
    filters,
    recordsPagination,
    isAuthenticated,
    isLoading,
    currentRecord,
    visibleMenus,
    currentRoles,
    tokenRoleLabels,
    inferredRoleLabels,
    roleSourceLabel,
    claimPreviewEntries,
    tokenClaimKeysText,
    roleClaimKeysText,
    displayedRoles,
    canUpload,
    canReadImages,
    canReview,
    canFinalize,
    canViewAccessPanel,
    canViewAuditLogs,
    hasWorkbenchAccess,
    configuredRoleClaimNamesText,
    roleClaimAlignmentTagType,
    roleClaimAlignmentLabel,
    navigationItems,
    dashboardStats,
    clinicalInsights,
    beginSignIn,
    beginSignOut,
    fetchRecords,
    fetchAnalysisRecord,
    handleUpload,
    applyFilters,
    resetFilters,
    handleRecordsPageChange,
    handleRecordsPageSizeChange,
    handleReviewSubmit,
    handleFinalizeSubmit,
    refreshAuditLogs,
    applyAuditFilters,
    resetAuditFilters,
    handleAuditPageChange,
    handleAuditPageSizeChange,
    refreshDashboardSummary
  }
}
