import { http } from './http'
import type {
  DatasetCatalog,
  DatasetCatalogPayload,
  DatasetFilters,
  DatasetImportPayload,
  DatasetImportRecord,
  DatasetSampleRecord,
  DatasetSplitPayload,
  ModelEvaluationPayload,
  ModelEvaluationRecord,
  PaginatedDatasetImportsResult,
  PaginatedDatasetSamplesResult,
  PaginatedDatasetsResult,
  PaginatedModelEvaluationsResult,
} from '../types/dataset'
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

export async function listDatasetImports(
  datasetId: string,
  pagination?: { limit?: number; offset?: number },
): Promise<PaginatedDatasetImportsResult> {
  const response = await http.get<{ code: number; data: DatasetImportRecord[]; meta?: PaginationMeta }>(
    `/api/v1/datasets/${datasetId}/imports`,
    { params: pagination },
  )
  return {
    items: response.data.data,
    meta: normalizeMeta(response.data.meta, response.data.data.length, pagination),
  }
}

export async function createDatasetImport(datasetId: string, payload: DatasetImportPayload) {
  const response = await http.post<{ code: number; data: DatasetImportRecord }>(`/api/v1/datasets/${datasetId}/imports`, payload)
  return response.data.data
}

export async function uploadDatasetZip(importId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await http.post<{ code: number; data: DatasetImportRecord }>(
    `/api/v1/dataset-imports/${importId}/upload-zip`,
    formData,
  )
  return response.data.data
}

export async function listDatasetSamples(
  importId: string,
  pagination?: { limit?: number; offset?: number },
): Promise<PaginatedDatasetSamplesResult> {
  const response = await http.get<{ code: number; data: DatasetSampleRecord[]; meta?: PaginationMeta }>(
    `/api/v1/dataset-imports/${importId}/samples`,
    { params: pagination },
  )
  return {
    items: response.data.data,
    meta: normalizeMeta(response.data.meta, response.data.data.length, pagination),
  }
}

export async function splitDatasetImport(importId: string, payload: DatasetSplitPayload) {
  const response = await http.post<{ code: number; data: Record<string, number> }>(
    `/api/v1/dataset-imports/${importId}/split`,
    payload,
  )
  return response.data.data
}

export async function listModelEvaluations(
  filters?: { dataset_id?: string; import_id?: string },
  pagination?: { limit?: number; offset?: number },
): Promise<PaginatedModelEvaluationsResult> {
  const params = Object.fromEntries(
    Object.entries({ ...(filters ?? {}), ...(pagination ?? {}) }).filter(([, value]) => value !== '' && value !== undefined && value !== null),
  )
  const response = await http.get<{ code: number; data: ModelEvaluationRecord[]; meta?: PaginationMeta }>('/api/v1/model-evaluations', {
    params,
  })
  return {
    items: response.data.data,
    meta: normalizeMeta(response.data.meta, response.data.data.length, pagination),
  }
}

export async function createModelEvaluation(payload: ModelEvaluationPayload) {
  const response = await http.post<{ code: number; data: ModelEvaluationRecord }>('/api/v1/model-evaluations', payload)
  return response.data.data
}
