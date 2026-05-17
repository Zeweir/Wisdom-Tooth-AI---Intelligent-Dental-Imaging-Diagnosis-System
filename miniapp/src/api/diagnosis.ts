import { get, post, upload } from './http'

export interface QuizAnswer {
  question_id: number
  answer: string
}

export interface QuizResult {
  risk_level: 'low' | 'medium' | 'high'
  risk_score: number
  suggestions: string[]
  summary: string
  recommend_upload: boolean
}

export interface DiagnosisRecord {
  image_id: string
  patient_id: string
  image_type: string
  filename: string
  status: string
  report: {
    report_id: string
    content: string
    status: string
    doctor_review: string | null
  }
  created_at: string
}

export interface DiagnosisListResponse {
  items: DiagnosisRecord[]
  meta: { limit: number; offset: number; total: number }
}

export function submitQuiz(patientId: string, answers: QuizAnswer[]) {
  return post<QuizResult>('/api/v1/miniapp/quiz', {
    patient_id: patientId,
    answers,
  })
}

export function uploadImage(filePath: string, patientId: string) {
  return upload('/api/v1/images/upload', filePath, {
    patient_id: patientId,
    image_type: 'panoramic',
  })
}

export function getAnalysis(imageId: string) {
  return get<DiagnosisRecord>(`/api/v1/analysis/${imageId}`)
}

export function getPatientRecords(patientId: string, limit = 20, offset = 0) {
  return get<DiagnosisListResponse>(`/api/v1/patients/${patientId}/images?limit=${limit}&offset=${offset}`)
}
