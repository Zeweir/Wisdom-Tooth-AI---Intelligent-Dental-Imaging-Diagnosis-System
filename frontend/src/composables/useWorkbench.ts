import { computed, onMounted, ref, watch } from 'vue'
import { useLogto } from '@logto/vue'

import { getAuthProfile, getRbacModel } from '../api/auth'
import { logtoApiResource, setAccessTokenProvider } from '../api/http'
import type { AuthProfile, MenuCapability, RbacModel } from '../types/auth'
import type { WorkbenchContext } from '../workbench'
import { useWorkbenchAudit } from './workbench/useWorkbenchAudit'
import { useWorkbenchDashboard } from './workbench/useWorkbenchDashboard'
import { useWorkbenchRecords } from './workbench/useWorkbenchRecords'
import { useWorkbenchReports } from './workbench/useWorkbenchReports'
import { useWorkbenchUpload } from './workbench/useWorkbenchUpload'

type BasicClaims = {
  name?: string
  username?: string
  sub?: string
}

export function useWorkbench(): WorkbenchContext {
  const { fetchUserInfo, getAccessToken, getIdTokenClaims, isAuthenticated, isLoading, signIn, signOut } = useLogto()

  const authReady = ref(false)
  const displayName = ref('')
  const authProfile = ref<AuthProfile | null>(null)
  const rbacModel = ref<RbacModel | null>(null)
  const authScopes = ref<string[]>([])

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
      { key: 'home', label: '工作台', caption: '首页与核心诊疗入口', shortLabel: '工作台', to: '/' },
      { key: 'workspace', label: '影像工作站', caption: '上传、诊断、报告审核一体化', shortLabel: '工作站', to: '/workspace' },
    ]

    if (canReadImages.value) {
      items.push({ key: 'patients', label: '患者管理', caption: '患者列表、病例统计与历史影像', shortLabel: '患者', to: '/patients' })
      items.push({ key: 'datasets', label: '数据集中心', caption: '公开数据集、许可与适用任务', shortLabel: '数据集', to: '/datasets' })
    }
    if (canViewAccessPanel.value) {
      items.push({ key: 'access', label: '权限中心', caption: '角色配置与访问说明', shortLabel: '权限', to: '/access' })
    }
    if (canViewAuditLogs.value) {
      items.push({ key: 'audit', label: '审计中心', caption: '关键操作留痕日志', shortLabel: '审计', to: '/audit' })
    }
    items.push({ key: 'settings', label: '系统设置', caption: '角色与系统能力入口', shortLabel: '设置', to: '/settings' })

    return items
  })

  const audit = useWorkbenchAudit(canViewAuditLogs)
  const dashboard = useWorkbenchDashboard(canReadImages)
  const records = useWorkbenchRecords(canReadImages)
  const upload = useWorkbenchUpload({
    canUpload,
    canReadImages,
    getAccessToken,
    fetchRecords: records.fetchRecords,
    waitForAnalysisCompletion: records.waitForAnalysisCompletion,
    refreshAuditLogs: audit.refreshAuditLogs,
    refreshDashboardSummary: dashboard.refreshDashboardSummary,
  })
  const reports = useWorkbenchReports({
    canReview,
    canFinalize,
    currentRecord: records.currentRecord,
    reviewText: records.reviewText,
    fetchAnalysisRecord: records.fetchAnalysisRecord,
    fetchRecords: records.fetchRecords,
    refreshAuditLogs: audit.refreshAuditLogs,
    refreshDashboardSummary: dashboard.refreshDashboardSummary,
  })

  const dashboardStats = computed(() => [
    {
      label: '可见菜单',
      value: visibleMenus.value.length,
      description: '当前账号可访问的工作台模块数'
    },
    {
      label: '影像记录',
      value: records.records.value.length,
      description: '当前筛选条件下可查看的病例记录'
    },
    {
      label: '当前病灶数',
      value: records.currentRecord.value?.detections.length ?? 0,
      description: '当前选中记录中的检测结果数量'
    },
    {
      label: '审计事件',
      value: audit.auditLogs.value.length,
      description: '最近一次读取到的关键留痕数量'
    }
  ])
  const clinicalInsights = computed(() => {
    const fallbackDetections = records.records.value.flatMap((item) => item.detections)
    if (!dashboard.dashboardSummary.value) {
      const averageConfidence = fallbackDetections.length
        ? Math.round(
            (fallbackDetections.reduce((sum, item) => sum + item.confidence, 0) / fallbackDetections.length) * 100
          )
        : 0
      return [
        {
          label: '正式报告',
          value: records.records.value.filter((item) => item.report.status === 'finalized').length,
          description: '已由医生确认的报告数量'
        },
        {
          label: '平均置信度',
          value: averageConfidence,
          description: '当前病例列表内 AI 检测平均置信度'
        },
        {
          label: '处理中',
          value: records.records.value.filter((item) => item.status === 'processing').length,
          description: '仍在等待 AI 分析完成的影像'
        }
      ]
    }

    return [
      {
        label: '患者档案',
        value: dashboard.dashboardSummary.value.total_patients,
        description: `近 7 天新增 ${dashboard.dashboardSummary.value.recent_patients} 位患者`
      },
      {
        label: '公开数据集',
        value: dashboard.dashboardSummary.value.dataset_count,
        description: `开放可访问 ${dashboard.dashboardSummary.value.open_dataset_count} 个，覆盖 ${dashboard.dashboardSummary.value.covered_disease_count} 类标签`
      },
      {
        label: '处理中',
        value: dashboard.dashboardSummary.value.processing_images,
        description: '仍处于 AI 分析中的影像记录'
      }
    ]
  })

  function normalizeAccessToken(token: string | undefined | null) {
    return token ?? null
  }

  async function refreshAuthState() {
    if (!isAuthenticated.value) {
      authProfile.value = null
      rbacModel.value = null
      audit.auditLogs.value = []
      displayName.value = ''
      authScopes.value = []
      dashboard.dashboardSummary.value = null
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
      await audit.refreshAuditLogs()
    } else {
      audit.auditLogs.value = []
    }
    await dashboard.refreshDashboardSummary()
    authReady.value = true
  }

  async function beginSignIn() {
    await signIn(`${window.location.origin}/callback`)
  }

  async function beginSignOut() {
    await signOut(window.location.origin)
  }

  watch(isAuthenticated, async () => {
    await refreshAuthState()
    if (!isAuthenticated.value) {
      records.clearRecords()
      dashboard.dashboardSummary.value = null
      return
    }
    await records.fetchRecords()
    await dashboard.refreshDashboardSummary()
    if (records.selectedImageId.value) {
      await records.fetchAnalysisRecord(records.selectedImageId.value)
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
      await records.fetchRecords()
      await dashboard.refreshDashboardSummary()
      if (records.selectedImageId.value) {
        await records.fetchAnalysisRecord(records.selectedImageId.value)
      }
    }
  })

  return {
    loading: upload.loading,
    records: records.records,
    selectedImageId: records.selectedImageId,
    reviewText: records.reviewText,
    socketEvents: upload.socketEvents,
    authReady,
    displayName,
    authProfile,
    rbacModel,
    auditLogs: audit.auditLogs,
    auditFilters: audit.auditFilters,
    auditPagination: audit.auditPagination,
    authScopes,
    dashboardSummary: dashboard.dashboardSummary,
    filters: records.filters,
    recordsPagination: records.recordsPagination,
    isAuthenticated,
    isLoading,
    currentRecord: records.currentRecord,
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
    fetchRecords: records.fetchRecords,
    fetchAnalysisRecord: records.fetchAnalysisRecord,
    handleUpload: upload.handleUpload,
    applyFilters: records.applyFilters,
    resetFilters: records.resetFilters,
    handleRecordsPageChange: records.handleRecordsPageChange,
    handleRecordsPageSizeChange: records.handleRecordsPageSizeChange,
    handleReviewSubmit: reports.handleReviewSubmit,
    handleFinalizeSubmit: reports.handleFinalizeSubmit,
    refreshAuditLogs: audit.refreshAuditLogs,
    applyAuditFilters: audit.applyAuditFilters,
    resetAuditFilters: audit.resetAuditFilters,
    handleAuditPageChange: audit.handleAuditPageChange,
    handleAuditPageSizeChange: audit.handleAuditPageSizeChange,
    refreshDashboardSummary: dashboard.refreshDashboardSummary
  }
}
