import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import { getAnalysis, listImages } from '../api/analysis'
import { listPatients } from '../api/patients'
import type { AnalysisItem } from '../types/analysis'
import type { PatientRecord } from '../types/patient'
import { useWorkbenchContext } from '../workbench'

export type GlobalSearchOption = {
  value: string
  label: string
  caption: string
  type: 'image' | 'patient'
  id: string
}

export function useGlobalSearch() {
  const router = useRouter()
  const workbench = useWorkbenchContext()
  const keyword = ref('')
  const searching = ref(false)

  function imageOption(record: AnalysisItem): GlobalSearchOption {
    return {
      value: `${record.patient?.name ?? record.patient_id} ${record.filename}`,
      label: record.patient?.name ?? record.patient_id,
      caption: `病例 ${record.image_id} / ${record.filename}`,
      type: 'image',
      id: record.image_id,
    }
  }

  function patientOption(patient: PatientRecord): GlobalSearchOption {
    return {
      value: `${patient.name} ${patient.patient_id}`,
      label: patient.name,
      caption: `患者 ${patient.patient_id} / ${patient.image_count} 条影像`,
      type: 'patient',
      id: patient.patient_id,
    }
  }

  function matchesRecord(record: AnalysisItem, query: string) {
    const haystack = [
      record.image_id,
      record.filename,
      record.patient_id,
      record.patient?.name ?? '',
    ].join(' ').toLowerCase()
    return haystack.includes(query.toLowerCase())
  }

  async function buildOptions(query: string) {
    const trimmed = query.trim()
    if (!trimmed || !workbench.canReadImages.value) {
      return []
    }

    searching.value = true
    try {
      const [exactImage, patientResult, patientImageResult, recentImageResult] = await Promise.all([
        getAnalysis(trimmed).catch(() => null),
        listPatients(trimmed, { limit: 5, offset: 0 }).catch(() => ({ items: [] })),
        listImages({ patient_id: trimmed }, { limit: 5, offset: 0 }).catch(() => ({ items: [] })),
        listImages({}, { limit: 80, offset: 0 }).catch(() => ({ items: [] })),
      ])

      const imageMap = new Map<string, AnalysisItem>()
      if (exactImage) {
        imageMap.set(exactImage.image_id, exactImage)
      }
      for (const record of patientImageResult.items) {
        imageMap.set(record.image_id, record)
      }
      for (const record of recentImageResult.items.filter((item) => matchesRecord(item, trimmed))) {
        imageMap.set(record.image_id, record)
      }

      return [
        ...Array.from(imageMap.values()).slice(0, 6).map(imageOption),
        ...patientResult.items.slice(0, 5).map(patientOption),
      ].slice(0, 8)
    } finally {
      searching.value = false
    }
  }

  async function fetchSuggestions(query: string, callback: (options: GlobalSearchOption[]) => void) {
    callback(await buildOptions(query))
  }

  async function openOption(option: GlobalSearchOption) {
    keyword.value = ''
    if (option.type === 'image') {
      await router.push({ path: '/workspace', query: { image_id: option.id } })
      return
    }
    await router.push({ path: '/patients', query: { patient_id: option.id } })
  }

  async function submitSearch() {
    const options = await buildOptions(keyword.value)
    if (options.length === 0) {
      ElMessage.warning('未找到匹配的患者或病例')
      return
    }
    await openOption(options[0])
  }

  return {
    keyword,
    searching,
    fetchSuggestions,
    openOption,
    submitSearch,
  }
}
