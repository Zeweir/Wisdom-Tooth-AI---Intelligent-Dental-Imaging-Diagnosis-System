import { http } from './http'
import type { AuditLogItem, PaginatedAuditLogResult } from '../types/audit'

export async function getAuditLogs(params?: {
  limit?: number
  offset?: number
  action?: string
  resource_type?: string
  resource_id?: string
  actor_sub?: string
}): Promise<PaginatedAuditLogResult> {
  const requestParams = Object.fromEntries(
    Object.entries(params ?? {}).filter(([, value]) => value !== '' && value !== undefined && value !== null)
  )
  const response = await http.get<{
    code: number
    data: AuditLogItem[]
    meta?: { limit: number; offset: number; total: number }
  }>('/api/v1/audit-logs', {
    params: requestParams
  })
  return {
    items: response.data.data,
    meta: response.data.meta ?? {
      limit: params?.limit ?? response.data.data.length,
      offset: params?.offset ?? 0,
      total: response.data.data.length
    }
  }
}
