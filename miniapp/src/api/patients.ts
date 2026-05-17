import { get } from './http'

export interface PatientRecord {
  patient_id: string
  name: string
  gender: string | null
  age: number | null
  phone: string | null
  notes: string | null
  image_count: number
  latest_image_at: string | null
  created_at: string
}

export interface PatientListResponse {
  data: PatientRecord[]
  meta: { limit: number; offset: number; total: number }
}

export function listPatients(keyword = '', limit = 20, offset = 0) {
  const query = `limit=${limit}&offset=${offset}`
  const full = keyword ? `${query}&keyword=${encodeURIComponent(keyword)}` : query
  return get<PatientListResponse>(`/api/v1/patients?${full}`)
}

export function getPatient(patientId: string) {
  return get<{ data: PatientRecord }>(`/api/v1/patients/${patientId}`)
}

export function getPatientImages(patientId: string, limit = 20, offset = 0) {
  return get<{ data: any[]; meta: { limit: number; offset: number; total: number } }>(
    `/api/v1/patients/${patientId}/images?limit=${limit}&offset=${offset}`
  )
}
