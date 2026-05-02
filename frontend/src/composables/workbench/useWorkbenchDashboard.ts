import type { ComputedRef } from 'vue'
import { ref } from 'vue'

import { getDashboardSummary } from '../../api/analysis'
import type { DashboardSummary } from '../../types/analysis'

export function useWorkbenchDashboard(canReadImages: ComputedRef<boolean>) {
  const dashboardSummary = ref<DashboardSummary | null>(null)

  async function refreshDashboardSummary() {
    if (!canReadImages.value) {
      dashboardSummary.value = null
      return
    }
    try {
      dashboardSummary.value = await getDashboardSummary()
    } catch {
      dashboardSummary.value = null
    }
  }

  return {
    dashboardSummary,
    refreshDashboardSummary,
  }
}
