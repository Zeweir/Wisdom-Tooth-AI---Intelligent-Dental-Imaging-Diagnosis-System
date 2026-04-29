import { http } from './http'
import type { DatasetCatalog, DatasetCatalogPayload, DatasetFilters, PaginatedDatasetsResult } from '../types/dataset'
import type { PaginationMeta } from '../types/analysis'

function normalizeMeta(meta: PaginationMeta | undefined, fallbackLength: number, pagination?: { limit?: number; offset?: number }) {
  return meta ?? {
    limit: pagination?.limit ?? fallbackLength,
    offset: pagination?.offset ?? 0,
    total: fallbackLength,
  }
}

export async function listDatasets(
  filters?: Partial<DatasetFilters>,
  pagination?: { limit?: number; offset?: number },
): Promise<PaginatedDatasetsResult> {
  const params = Object.fromEntries(
    Object.entries({ ...(filters ?? {}), ...(pagination ?? {}) }).filter(([, value]) => value !== '' && value !== undefined && value !== null),
  )
  const response = await http.get<{ code: number; data: DatasetCatalog[]; meta?: PaginationMeta }>('/api/v1/datasets', {
    params,
  })
  return {
    items: response.data.data,
    meta: normalizeMeta(response.data.meta, response.data.data.length, pagination),
  }
}

export async function createDataset(payload: DatasetCatalogPayload) {
  const response = await http.post<{ code: number; data: DatasetCatalog }>('/api/v1/datasets', payload)
  return response.data.data
}

export async function updateDataset(datasetId: string, payload: Partial<DatasetCatalogPayload>) {
  const response = await http.put<{ code: number; data: DatasetCatalog }>(`/api/v1/datasets/${datasetId}`, payload)
  return response.data.data
}

export async function getDataset(datasetId: string) {
  const response = await http.get<{ code: number; data: DatasetCatalog }>(`/api/v1/datasets/${datasetId}`)
  return response.data.data
}

export async function seedPublicDatasets() {
  const response = await http.post<{ code: number; data: { created: number; skipped: number } }>('/api/v1/datasets/seed-public')
  return response.data.data
}
