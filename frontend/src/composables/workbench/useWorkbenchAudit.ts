import type { ComputedRef } from 'vue'
import { ref } from 'vue'

import { getAuditLogs } from '../../api/audit'
import type { AuditLogFilters, AuditLogItem, AuditLogPagination } from '../../types/audit'

export function useWorkbenchAudit(canViewAuditLogs: ComputedRef<boolean>) {
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

  return {
    auditLogs,
    auditFilters,
    auditPagination,
    refreshAuditLogs,
    applyAuditFilters,
    resetAuditFilters,
    handleAuditPageChange,
    handleAuditPageSizeChange,
  }
}
