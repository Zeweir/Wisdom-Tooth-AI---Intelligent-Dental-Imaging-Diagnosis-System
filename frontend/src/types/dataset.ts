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
