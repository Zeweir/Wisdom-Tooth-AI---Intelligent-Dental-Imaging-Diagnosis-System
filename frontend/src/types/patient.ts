import type { AnalysisItem, PaginationMeta } from './analysis'

export interface PatientSummary {
  patient_id: string
  name: string
  gender: string | null
  age: number | null
  phone: string | null
}

export interface PatientRecord extends PatientSummary {
  notes: string | null
  image_count: number
  latest_image_at: string | null
  created_at: string
  updated_at: string
}

export interface PatientFormPayload {
  patient_id: string
  name: string
  gender?: string | null
  age?: number | null
  phone?: string | null
  notes?: string | null
}

export interface PatientUpdatePayload {
  name?: string | null
  gender?: string | null
  age?: number | null
  phone?: string | null
  notes?: string | null
}

export interface PaginatedPatientsResult {
  items: PatientRecord[]
  meta: PaginationMeta
}

export interface PaginatedPatientImagesResult {
  items: AnalysisItem[]
  meta: PaginationMeta
}
