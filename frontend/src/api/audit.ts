import { http } from './http'
import type { AuditLogItem } from '../types/audit'

export async function getAuditLogs(params?: {
  limit?: number
  action?: string
  resource_type?: string
}) {
  const response = await http.get<{ code: number; data: AuditLogItem[] }>('/api/v1/audit-logs', {
    params
  })
  return response.data.data
}
