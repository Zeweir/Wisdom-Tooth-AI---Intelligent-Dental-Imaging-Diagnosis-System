import { get } from './http'

export interface DatasetRecord {
  dataset_id: string
  name: string
  source_name: string
  homepage_url: string
  paper_url: string | null
  license: string | null
  image_type: string
  task_types: string[]
  disease_tags: string[]
  sample_size: string | null
  annotation_format: string | null
  access_status: string
  priority: string
  notes: string | null
  created_at: string
}

export interface DatasetListResponse {
  data: DatasetRecord[]
  meta: { limit: number; offset: number; total: number }
}

export function listDatasets(keyword = '', taskType = '', disease = '', limit = 20, offset = 0) {
  let query = `limit=${limit}&offset=${offset}`
  if (keyword) query += `&keyword=${encodeURIComponent(keyword)}`
  if (taskType) query += `&task_type=${encodeURIComponent(taskType)}`
  if (disease) query += `&disease=${encodeURIComponent(disease)}`
  return get<DatasetListResponse>(`/api/v1/datasets?${query}`)
}
