import type { ComputedRef } from 'vue'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

import { createAnalysisSocket, uploadImage } from '../../api/analysis'
import { logtoApiResource } from '../../api/http'
import type { AnalysisItem } from '../../types/analysis'

interface WorkbenchUploadOptions {
  canUpload: ComputedRef<boolean>
  canReadImages: ComputedRef<boolean>
  getAccessToken: (resource?: string) => Promise<string | undefined>
  fetchRecords: () => Promise<void>
  waitForAnalysisCompletion: (imageId: string) => Promise<AnalysisItem | null>
  refreshAuditLogs: () => Promise<void>
  refreshDashboardSummary: () => Promise<void>
}

export function useWorkbenchUpload(options: WorkbenchUploadOptions) {
  const loading = ref(false)
  const socketEvents = ref<string[]>([])

  function normalizeAccessToken(token: string | undefined | null) {
    return token ?? null
  }

  function connectProgress(imageId: string) {
    socketEvents.value = []
    options.getAccessToken(logtoApiResource).then((rawAccessToken) => {
      const accessToken = normalizeAccessToken(rawAccessToken)
      if (!accessToken) {
        socketEvents.value.push('analysis.socket_error / missing_token')
        return
      }
      const socket = createAnalysisSocket(imageId, accessToken)
      socket.onmessage = (event: MessageEvent<string>) => {
        const payload = JSON.parse(event.data) as { event: string; status: string }
        socketEvents.value.push(`${payload.event} / ${payload.status}`)
      }
      socket.onerror = () => {
        socketEvents.value.push('analysis.socket_error / unavailable')
      }
    })
  }

  async function handleUpload(payload: { file: File; patientId: string; patientName?: string; imageType: AnalysisItem['image_type'] }) {
    if (!options.canUpload.value) {
      ElMessage.warning('你当前没有上传影像的权限')
      return
    }
    loading.value = true
    try {
      const result = await uploadImage(payload)
      ElMessage.success('上传成功')
      connectProgress(result.image_id)
      const completed = await options.waitForAnalysisCompletion(result.image_id)
      if (!completed) {
        ElMessage.warning('分析仍在处理中，请稍后刷新查看结果')
      }
      if (options.canReadImages.value) {
        await options.fetchRecords()
      }
      await options.refreshDashboardSummary()
      await options.refreshAuditLogs()
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    socketEvents,
    handleUpload,
  }
}
