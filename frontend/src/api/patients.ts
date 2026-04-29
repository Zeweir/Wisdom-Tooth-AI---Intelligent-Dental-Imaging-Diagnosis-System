import { http } from './http'
import type {
  PaginatedPatientImagesResult,
  PaginatedPatientsResult,
  PatientFormPayload,
  PatientRecord,
  PatientUpdatePayload,
} from '../types/patient'
import type { AnalysisItem, PaginationMeta } from '../types/analysis'

function normalizeMeta(meta: PaginationMeta | undefined, fallbackLength: number, pagination?: { limit?: number; offset?: number }) {
  return meta ?? {
    limit: pagination?.limit ?? fallbackLength,
    offset: pagination?.offset ?? 0,
    total: fallbackLength,
  }
}

export async function listPatients(
  keyword?: string,
  pagination?: { limit?: number; offset?: number },
): Promise<PaginatedPatientsResult> {
  const params = Object.fromEntries(
    Object.entries({ keyword, ...(pagination ?? {}) }).filter(([, value]) => value !== '' && value !== undefined && value !== null),
  )
  const response = await http.get<{ code: number; data: PatientRecord[]; meta?: PaginationMeta }>('/api/v1/patients', {
    params,
  })
  return {
    items: response.data.data,
    meta: normalizeMeta(response.data.meta, response.data.data.length, pagination),
  }
}

export async function createPatient(payload: PatientFormPayload) {
  const response = await http.post<{ code: number; data: PatientRecord }>('/api/v1/patients', payload)
  return response.data.data
}

export async function updatePatient(patientId: string, payload: PatientUpdatePayload) {
  const response = await http.put<{ code: number; data: PatientRecord }>(`/api/v1/patients/${patientId}`, payload)
  return response.data.data
}

export async function getPatient(patientId: string) {
  const response = await http.get<{ code: number; data: PatientRecord }>(`/api/v1/patients/${patientId}`)
  return response.data.data
}

export async function listPatientImages(
  patientId: string,
  pagination?: { limit?: number; offset?: number },
): Promise<PaginatedPatientImagesResult> {
  const response = await http.get<{ code: number; data: AnalysisItem[]; meta?: PaginationMeta }>(
    `/api/v1/patients/${patientId}/images`,
    { params: pagination },
  )
  return {
    items: response.data.data,
    meta: normalizeMeta(response.data.meta, response.data.data.length, pagination),
  }
}
