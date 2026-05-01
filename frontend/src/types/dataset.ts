import type { PaginationMeta } from './analysis'

export interface DatasetCatalog {
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
  updated_at: string
}

export interface DatasetFilters {
  keyword: string
  task_type: string
  disease: string
}

export interface DatasetCatalogPayload {
  name: string
  source_name: string
  homepage_url: string
  paper_url?: string | null
  license?: string | null
  image_type: string
  task_types: string[]
  disease_tags: string[]
  sample_size?: string | null
  annotation_format?: string | null
  access_status: string
  priority: string
  notes?: string | null
}

export interface PaginatedDatasetsResult {
  items: DatasetCatalog[]
  meta: PaginationMeta
}

export type DatasetImportMethod = 'local_directory' | 'zip_upload' | 'manual_summary' | 'url_download'

export interface DatasetImportRecord {
  import_id: string
  dataset_id: string
  import_method: DatasetImportMethod
  source_path: string | null
  storage_provider: string | null
  storage_bucket: string | null
  storage_object_key: string | null
  sample_count: number
  annotation_format: string | null
  image_type: string
  status: string
  error_message: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface DatasetImportPayload {
  import_method: DatasetImportMethod
  source_path?: string | null
  sample_count: number
  annotation_format?: string | null
  image_type: string
  notes?: string | null
}

export interface DatasetImportDownloadPayload {
  source_url: string
  sample_count: number
  annotation_format?: string | null
  image_type: string
  notes?: string | null
}

export interface DatasetSampleRecord {
  sample_id: string
  import_id: string
  dataset_id: string
  filename: string
  file_type: string
  image_type: string
  annotation_status: string
  split: string | null
  label_summary: Record<string, unknown>
  storage_object_key: string | null
  created_at: string
}

export interface DatasetSplitPayload {
  train_ratio: number
  val_ratio: number
  test_ratio: number
}

export interface ModelEvaluationRecord {
  evaluation_id: string
  model_name: string
  model_version: string
  dataset_id: string | null
  import_id: string | null
  precision: number | null
  recall: number | null
  map_score: number | null
  f1_score: number | null
  sample_count: number | null
  notes: string | null
  created_at: string
}

export interface ModelEvaluationPayload {
  model_name: string
  model_version: string
  dataset_id?: string | null
  import_id?: string | null
  precision?: number | null
  recall?: number | null
  map_score?: number | null
  f1_score?: number | null
  sample_count?: number | null
  notes?: string | null
}

export interface PaginatedDatasetImportsResult {
  items: DatasetImportRecord[]
  meta: PaginationMeta
}

export interface PaginatedDatasetSamplesResult {
  items: DatasetSampleRecord[]
  meta: PaginationMeta
}

export interface PaginatedModelEvaluationsResult {
  items: ModelEvaluationRecord[]
  meta: PaginationMeta
}
