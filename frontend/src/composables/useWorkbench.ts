import { computed, onMounted, ref, watch } from 'vue'

import { getAuthProfile, getRbacModel } from '../api/auth'
import { getStoredToken } from '../api/http'
import type { AuthProfile, MenuCapability, RbacModel } from '../types/auth'
import type { DisplayRole, WorkbenchContext } from '../workbench'
import { useAuth } from './useAuth'
import { useWorkbenchAudit } from './workbench/useWorkbenchAudit'
import { useWorkbenchDashboard } from './workbench/useWorkbenchDashboard'
import { useWorkbenchRecords } from './workbench/useWorkbenchRecords'
import { useWorkbenchReports } from './workbench/useWorkbenchReports'
import { useWorkbenchUpload } from './workbench/useWorkbenchUpload'

export function useWorkbench(): WorkbenchContext {
  const auth = useAuth()

  const authProfile = ref<AuthProfile | null>(null)
  const rbacModel = ref<RbacModel | null>(null)
  const authScopes = ref<string[]>([])

  const visibleMenus = computed(() => authProfile.value?.menus.filter((item: MenuCapability) => item.visible) ?? [])
  const currentRoles = computed(() => authProfile.value?.roles ?? [])
  const displayedRoles = computed<DisplayRole[]>(() => {
    const definitions = rbacModel.value?.roles ?? []
    return currentRoles.value.map((roleKey) => {
      const matched = definitions.find((item) => item.key === roleKey)
      return { key: roleKey, label: matched?.label ?? roleKey }
    })
  })
  const canUpload = computed(() => visibleMenus.value.some((item) => item.key === 'upload'))
  const canReadImages = computed(() => visibleMenus.value.some((item) => item.key === 'records'))
  const canReview = computed(() => visibleMenus.value.some((item) => item.key === 'review'))
  const canFinalize = computed(() => authScopes.value.includes('finalize:reports'))
  const canViewAccessPanel = computed(() => visibleMenus.value.some((item) => item.key === 'access'))
  const canViewAuditLogs = computed(() => visibleMenus.value.some((item) => item.key === 'audit'))
  const hasWorkbenchAccess = computed(() => canUpload.value || canReadImages.value || canReview.value)

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
    getAccessToken: async () => getStoredToken(),
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
    { label: '可见菜单', value: visibleMenus.value.length, description: '当前账号可访问的工作台模块数' },
    { label: '影像记录', value: records.records.value.length, description: '当前筛选条件下可查看的病例记录' },
    { label: '当前病灶数', value: records.currentRecord.value?.detections.length ?? 0, description: '当前选中记录中的检测结果数量' },
    { label: '审计事件', value: audit.auditLogs.value.length, description: '最近一次读取到的关键留痕数量' },
  ])
  const clinicalInsights = computed(() => {
    if (!dashboard.dashboardSummary.value) {
      const fallbackDetections = records.records.value.flatMap((item) => item.detections)
      const averageConfidence = fallbackDetections.length
        ? Math.round((fallbackDetections.reduce((sum, item) => sum + item.confidence, 0) / fallbackDetections.length) * 100)
        : 0
      return [
        { label: '正式报告', value: records.records.value.filter((item) => item.report.status === 'finalized').length, description: '已由医生确认的报告数量' },
        { label: '平均置信度', value: averageConfidence, description: '当前病例列表内 AI 检测平均置信度' },
        { label: '处理中', value: records.records.value.filter((item) => item.status === 'processing').length, description: '仍在等待 AI 分析完成的影像' },
      ]
    }
    return [
      { label: '患者档案', value: dashboard.dashboardSummary.value.total_patients, description: `近 7 天新增 ${dashboard.dashboardSummary.value.recent_patients} 位患者` },
      { label: '公开数据集', value: dashboard.dashboardSummary.value.dataset_count, description: `开放可访问 ${dashboard.dashboardSummary.value.open_dataset_count} 个，覆盖 ${dashboard.dashboardSummary.value.covered_disease_count} 类标签` },
      { label: '处理中', value: dashboard.dashboardSummary.value.processing_images, description: '仍处于 AI 分析中的影像记录' },
    ]
  })

  async function refreshAuthState() {
    if (!auth.isAuthenticated.value) {
      authProfile.value = null
      rbacModel.value = null
      audit.auditLogs.value = []
      authScopes.value = []
      dashboard.dashboardSummary.value = null
      auth.authReady.value = true
      return
    }

    try {
      const [profile, model] = await Promise.all([getAuthProfile(), getRbacModel()])
      authProfile.value = profile
      rbacModel.value = model
      authScopes.value = profile.permissions
      if (profile.menus.some((item: MenuCapability) => item.key === 'audit' && item.visible)) {
        await audit.refreshAuditLogs()
      } else {
        audit.auditLogs.value = []
      }
      await dashboard.refreshDashboardSummary()
    } catch {
      auth.logout()
    }
  }

  async function beginSignIn() {
    // handled by router redirect to /login
  }

  async function beginSignOut() {
    auth.logout()
    window.location.replace('/login')
  }

  watch(auth.isAuthenticated, async (val) => {
    await refreshAuthState()
    if (!val) {
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
    await refreshAuthState()
    if (auth.isAuthenticated.value) {
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
    authReady: auth.authReady,
    displayName: computed(() => auth.user.value?.display_name ?? '未登录用户'),
    authProfile,
    rbacModel,
    auditLogs: audit.auditLogs,
    auditFilters: audit.auditFilters,
    auditPagination: audit.auditPagination,
    authScopes,
    dashboardSummary: dashboard.dashboardSummary,
    filters: records.filters,
    recordsPagination: records.recordsPagination,
    isAuthenticated: auth.isAuthenticated,
    isLoading: auth.isLoading,
    currentRecord: records.currentRecord,
    visibleMenus,
    currentRoles,
    displayedRoles,
    canUpload,
    canReadImages,
    canReview,
    canFinalize,
    canViewAccessPanel,
    canViewAuditLogs,
    hasWorkbenchAccess,
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
    refreshDashboardSummary: dashboard.refreshDashboardSummary,
  }
}
