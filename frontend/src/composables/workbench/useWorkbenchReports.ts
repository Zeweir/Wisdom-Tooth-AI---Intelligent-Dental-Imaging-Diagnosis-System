import type { ComputedRef, Ref } from 'vue'
import { ElMessage } from 'element-plus'

import { reviewReport } from '../../api/analysis'
import type { AnalysisItem } from '../../types/analysis'

interface WorkbenchReportsOptions {
  canReview: ComputedRef<boolean>
  canFinalize: ComputedRef<boolean>
  currentRecord: ComputedRef<AnalysisItem | null>
  reviewText: Ref<string>
  fetchAnalysisRecord: (imageId: string) => Promise<void>
  fetchRecords: () => Promise<void>
  refreshAuditLogs: () => Promise<void>
  refreshDashboardSummary: () => Promise<void>
}

export function useWorkbenchReports(options: WorkbenchReportsOptions) {
  async function handleReviewSubmit() {
    if (!options.canReview.value) {
      ElMessage.warning('你当前没有审核报告的权限')
      return
    }
    if (!options.currentRecord.value) {
      ElMessage.warning('请先选择分析记录')
      return
    }

    await reviewReport(options.currentRecord.value.report.report_id, {
      doctor_review: options.reviewText.value,
      modified_findings: options.currentRecord.value.detections,
      status: 'doctor_reviewed'
    })
    ElMessage.success('审核意见已提交')
    await options.fetchAnalysisRecord(options.currentRecord.value.image_id)
    await options.refreshAuditLogs()
    await options.refreshDashboardSummary()
  }

  async function handleFinalizeSubmit() {
    if (!options.canFinalize.value) {
      ElMessage.warning('你当前没有正式确认报告的权限')
      return
    }
    if (!options.currentRecord.value) {
      ElMessage.warning('请先选择分析记录')
      return
    }

    await reviewReport(options.currentRecord.value.report.report_id, {
      doctor_review: options.reviewText.value,
      modified_findings: options.currentRecord.value.detections,
      status: 'finalized'
    })
    ElMessage.success('报告已正式确认')
    await options.fetchAnalysisRecord(options.currentRecord.value.image_id)
    await options.fetchRecords()
    await options.refreshAuditLogs()
    await options.refreshDashboardSummary()
  }

  return {
    handleReviewSubmit,
    handleFinalizeSubmit,
  }
}
