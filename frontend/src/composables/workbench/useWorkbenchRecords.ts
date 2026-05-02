import type { ComputedRef } from 'vue'
import { computed, ref } from 'vue'

import { getAnalysis, listImages } from '../../api/analysis'
import type { AnalysisFilters, AnalysisItem, PaginationMeta } from '../../types/analysis'

export function useWorkbenchRecords(canReadImages: ComputedRef<boolean>) {
  const records = ref<AnalysisItem[]>([])
  const selectedImageId = ref('')
  const reviewText = ref('')
  const recordsPagination = ref<PaginationMeta>({
    limit: 10,
    offset: 0,
    total: 0
  })
  const filters = ref<AnalysisFilters>({
    patient_id: '',
    image_type: '',
    report_status: ''
  })
  const currentRecord = computed(() => records.value.find((item) => item.image_id === selectedImageId.value) ?? null)

  function clearRecords() {
    records.value = []
    selectedImageId.value = ''
    reviewText.value = ''
    recordsPagination.value = { ...recordsPagination.value, offset: 0, total: 0 }
  }

  async function fetchRecords() {
    if (!canReadImages.value) {
      clearRecords()
      return
    }
    const result = await listImages(filters.value, {
      limit: recordsPagination.value.limit,
      offset: recordsPagination.value.offset
    })
    records.value = result.items
    recordsPagination.value = result.meta
    if (selectedImageId.value && !records.value.some((item) => item.image_id === selectedImageId.value)) {
      selectedImageId.value = ''
      reviewText.value = ''
    }
    if (!selectedImageId.value && records.value.length > 0) {
      selectedImageId.value = records.value[0].image_id
    }
  }

  async function fetchAnalysisRecord(imageId: string) {
    if (!canReadImages.value) {
      return
    }
    const current = await getAnalysis(imageId)
    const index = records.value.findIndex((item) => item.image_id === imageId)
    if (index >= 0) {
      records.value[index] = current
    } else {
      records.value.unshift(current)
    }
    selectedImageId.value = imageId
    reviewText.value = current.report.doctor_review ?? ''
  }

  async function waitForAnalysisCompletion(imageId: string) {
    if (!canReadImages.value) {
      return null
    }
    for (let attempt = 0; attempt < 10; attempt += 1) {
      const current = await getAnalysis(imageId)
      const index = records.value.findIndex((item) => item.image_id === imageId)
      if (index >= 0) {
        records.value[index] = current
      } else {
        records.value.unshift(current)
      }
      selectedImageId.value = imageId
      reviewText.value = current.report.doctor_review ?? ''
      if (current.status !== 'processing') {
        return current
      }
      await new Promise((resolve) => window.setTimeout(resolve, 800))
    }
    return null
  }

  async function applyFilters() {
    if (!canReadImages.value) {
      return
    }
    recordsPagination.value = { ...recordsPagination.value, offset: 0 }
    await fetchRecords()
    if (selectedImageId.value) {
      await fetchAnalysisRecord(selectedImageId.value)
    }
  }

  async function resetFilters() {
    filters.value = {
      patient_id: '',
      image_type: '',
      report_status: ''
    }
    await applyFilters()
  }

  async function handleRecordsPageChange(page: number) {
    recordsPagination.value = {
      ...recordsPagination.value,
      offset: (page - 1) * recordsPagination.value.limit
    }
    await fetchRecords()
  }

  async function handleRecordsPageSizeChange(pageSize: number) {
    recordsPagination.value = {
      ...recordsPagination.value,
      limit: pageSize,
      offset: 0
    }
    await fetchRecords()
  }

  return {
    records,
    selectedImageId,
    reviewText,
    recordsPagination,
    filters,
    currentRecord,
    clearRecords,
    fetchRecords,
    fetchAnalysisRecord,
    waitForAnalysisCompletion,
    applyFilters,
    resetFilters,
    handleRecordsPageChange,
    handleRecordsPageSizeChange,
  }
}
