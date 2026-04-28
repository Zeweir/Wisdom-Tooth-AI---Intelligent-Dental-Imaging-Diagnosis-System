export interface AuditLogItem {
  audit_log_id: string;
  actor_sub: string;
  actor_client_id: string | null;
  actor_organization_id: string | null;
  actor_roles: string[];
  action: string;
  resource_type: string;
  resource_id: string;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogFilters {
  action: string;
  resource_type: string;
  resource_id: string;
  actor_sub: string;
}

export interface AuditLogPagination {
  limit: number;
  offset: number;
  total: number;
}

export interface PaginatedAuditLogResult {
  items: AuditLogItem[];
  meta: AuditLogPagination;
}
