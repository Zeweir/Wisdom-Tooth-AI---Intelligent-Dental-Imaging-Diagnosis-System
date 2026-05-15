import type { ComputedRef, InjectionKey, Ref } from 'vue'
import { inject } from 'vue'

import type { AnalysisFilters, AnalysisItem, DashboardSummary, PaginationMeta } from './types/analysis'
import type { AuditLogFilters, AuditLogItem, AuditLogPagination } from './types/audit'
import type { AuthProfile, MenuCapability, RbacModel } from './types/auth'

export interface NavigationItem {
  key: 'home' | 'workspace' | 'patients' | 'upload' | 'diagnosis' | 'reports' | 'settings' | 'datasets' | 'access' | 'audit' | 'system'
  label: string
  caption: string
  shortLabel: string
  to: string
}

export interface DashboardStat {
  label: string
  value: number
  description: string
}

export interface DisplayRole {
  key: string
  label: string
}

export interface WorkbenchContext {
  loading: Ref<boolean>
  records: Ref<AnalysisItem[]>
  selectedImageId: Ref<string>
  reviewText: Ref<string>
  socketEvents: Ref<string[]>
  authReady: Ref<boolean>
  displayName: ComputedRef<string>
  authProfile: Ref<AuthProfile | null>
  rbacModel: Ref<RbacModel | null>
  auditLogs: Ref<AuditLogItem[]>
  auditFilters: Ref<AuditLogFilters>
  auditPagination: Ref<AuditLogPagination>
  authScopes: Ref<string[]>
  dashboardSummary: Ref<DashboardSummary | null>
  filters: Ref<AnalysisFilters>
  recordsPagination: Ref<PaginationMeta>
  isAuthenticated: ComputedRef<boolean>
  isLoading: Ref<boolean>
  currentRecord: ComputedRef<AnalysisItem | null>
  visibleMenus: ComputedRef<MenuCapability[]>
  currentRoles: ComputedRef<string[]>
  displayedRoles: ComputedRef<DisplayRole[]>
  canUpload: ComputedRef<boolean>
  canReadImages: ComputedRef<boolean>
  canReview: ComputedRef<boolean>
  canFinalize: ComputedRef<boolean>
  canViewAccessPanel: ComputedRef<boolean>
  canViewAuditLogs: ComputedRef<boolean>
  hasWorkbenchAccess: ComputedRef<boolean>
  navigationItems: ComputedRef<NavigationItem[]>
  dashboardStats: ComputedRef<DashboardStat[]>
  clinicalInsights: ComputedRef<DashboardStat[]>
  beginSignIn: () => Promise<void>
  beginSignOut: () => Promise<void>
  fetchRecords: () => Promise<void>
  fetchAnalysisRecord: (imageId: string) => Promise<void>
  handleUpload: (payload: { file: File; patientId: string; patientName?: string; imageType: AnalysisItem['image_type'] }) => Promise<void>
  applyFilters: () => Promise<void>
  resetFilters: () => Promise<void>
  handleRecordsPageChange: (page: number) => Promise<void>
  handleRecordsPageSizeChange: (pageSize: number) => Promise<void>
  handleReviewSubmit: () => Promise<void>
  handleFinalizeSubmit: () => Promise<void>
  refreshAuditLogs: () => Promise<void>
  applyAuditFilters: () => Promise<void>
  resetAuditFilters: () => Promise<void>
  handleAuditPageChange: (page: number) => Promise<void>
  handleAuditPageSizeChange: (pageSize: number) => Promise<void>
  refreshDashboardSummary: () => Promise<void>
}

export const workbenchKey: InjectionKey<WorkbenchContext> = Symbol('workbench')

export function useWorkbenchContext() {
  const context = inject(workbenchKey)
  if (!context) {
    throw new Error('Workbench context is not available')
  }
  return context
}
