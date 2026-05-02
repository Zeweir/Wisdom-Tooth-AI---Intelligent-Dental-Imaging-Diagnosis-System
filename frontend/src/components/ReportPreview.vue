<script setup lang="ts">
import type { AnalysisItem } from '../types/analysis'
import { downloadClinicalReport, printClinicalReport } from '../utils/report'

const props = defineProps<{
  record: AnalysisItem | null
}>()

</script>

<template>
  <el-empty v-if="!props.record" description="请选择一条报告记录" />
  <div v-else class="report-preview">
    <div class="report-preview-meta">
      <span>患者：{{ props.record.patient?.name ?? props.record.patient_id }}</span>
      <span>影像：{{ props.record.filename }}</span>
      <span>诊断时间：{{ new Date(props.record.updated_at).toLocaleString() }}</span>
    </div>
    <article class="report-box">
      <div class="sub-title">AI 诊断内容</div>
      <p class="clinical-copy">{{ props.record.report.content || '暂无 AI 诊断内容' }}</p>
    </article>
    <article class="report-box">
      <div class="sub-title">医生审核意见</div>
      <p class="clinical-copy">{{ props.record.report.doctor_review || '暂无医生审核意见' }}</p>
    </article>
    <div class="report-preview-actions">
      <el-button type="primary" @click="downloadClinicalReport(props.record)">下载报告</el-button>
      <el-button @click="printClinicalReport(props.record)">打印预览</el-button>
    </div>
  </div>
</template>
