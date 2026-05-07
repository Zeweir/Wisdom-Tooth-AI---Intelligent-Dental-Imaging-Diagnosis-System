<script setup lang="ts">
import { computed, ref } from 'vue'
import ReportRevisionDrawer from './ReportRevisionDrawer.vue'
import type { AnalysisItem } from '../types/analysis'
import { getReportStatusLabel, getReportStatusTagType } from '../utils/display'
import { downloadClinicalReport, printClinicalReport } from '../utils/report'

const props = defineProps<{
  currentRecord: AnalysisItem | null
  canReview: boolean
  canFinalizeReport: boolean
}>()

const reviewText = defineModel<string>('reviewText', { required: true })
const canSubmit = computed(() => Boolean(props.currentRecord) && props.canReview)
const canFinalize = computed(() => props.currentRecord?.report.status === 'doctor_reviewed' && props.canFinalizeReport)
const currentStatusLabel = computed(() => (props.currentRecord ? getReportStatusLabel(props.currentRecord.report.status) : ''))
const currentStatusTagType = computed(() => (props.currentRecord ? getReportStatusTagType(props.currentRecord.report.status) : 'info'))
const reviewTextLength = computed(() => reviewText.value.trim().length)
const reportTextLength = computed(() => props.currentRecord?.report.content.length ?? 0)
const revisionDrawerVisible = ref(false)
const reportSteps = computed(() => {
  const status = props.currentRecord?.report.status
  return [
    {
      key: 'draft',
      title: '报告草稿',
      description: 'AI 已根据影像和检测结果生成初稿',
      done: status !== 'processing',
    },
    {
      key: 'review',
      title: '医生意见',
      description: props.currentRecord?.report.doctor_review ? '已保存医生审核意见' : '等待医生补充判断',
      done: status === 'doctor_reviewed' || status === 'finalized',
    },
    {
      key: 'archive',
      title: '确认归档',
      description: status === 'finalized' ? '已形成正式报告' : '主任医生确认后归档',
      done: status === 'finalized',
    },
  ]
})

const emit = defineEmits<{
  submit: []
  finalize: []
}>()

function handlePrintReport() {
  if (!props.currentRecord) {
    return
  }
  printClinicalReport(props.currentRecord, reviewText.value)
}

function handleExportHtml() {
  if (!props.currentRecord) {
    return
  }
  void downloadClinicalReport(props.currentRecord, reviewText.value)
}
</script>

<template>
  <el-card class="panel" shadow="never">
    <template #header>
      <div class="panel-header">
        <span>报告审核</span>
        <el-tag type="warning">医生确认后方可作为正式报告</el-tag>
      </div>
    </template>

    <el-empty v-if="!currentRecord" description="请选择一条分析记录" />
    <template v-else>
      <div class="report-workflow-card">
        <div
          v-for="step in reportSteps"
          :key="step.key"
          class="report-workflow-step"
          :class="{ done: step.done }"
        >
          <span aria-hidden="true" />
          <strong>{{ step.title }}</strong>
          <small>{{ step.description }}</small>
        </div>
      </div>

      <article class="report-box clinical-report-draft">
        <div class="panel-header">
          <span>报告草稿</span>
          <div class="section-heading-tags">
            <el-tag :type="currentStatusTagType">{{ currentStatusLabel }}</el-tag>
            <el-tag type="info">{{ reportTextLength }} 字</el-tag>
            <el-tag v-if="currentRecord.report.pdf_variant" type="success">{{ currentRecord.report.pdf_variant }}</el-tag>
          </div>
        </div>
        <p>{{ currentRecord.report.structured_content.summary || currentRecord.report.content }}</p>
      </article>

      <article v-if="currentRecord.report.structured_content.key_findings.length > 0" class="report-box">
        <div class="panel-header">
          <span>AI 关键发现</span>
          <el-tag type="danger">{{ currentRecord.report.structured_content.high_priority_findings.length }} 个高优先关注</el-tag>
        </div>
        <div class="report-preview-points">
          <p v-for="item in currentRecord.report.structured_content.key_findings" :key="item" class="clinical-copy">{{ item }}</p>
        </div>
      </article>

      <article v-if="currentRecord.report.structured_content.follow_up_plan.length > 0" class="report-box">
        <div class="panel-header">
          <span>建议处理方案</span>
          <el-tag type="info">{{ currentRecord.report.structured_content.follow_up_plan.length }} 条</el-tag>
        </div>
        <div class="report-preview-points">
          <p v-for="item in currentRecord.report.structured_content.follow_up_plan" :key="item" class="clinical-copy">{{ item }}</p>
        </div>
      </article>

      <article v-if="currentRecord.report.structured_content.tooth_findings.length > 0" class="report-box">
        <div class="panel-header">
          <span>按牙位问题说明</span>
          <el-tag type="info">{{ currentRecord.report.structured_content.tooth_findings.length }} 个牙位</el-tag>
        </div>
        <div class="report-preview-points">
          <div
            v-for="group in currentRecord.report.structured_content.tooth_findings"
            :key="`${group.display_name}-${group.source}`"
            class="report-tooth-group"
          >
            <div class="panel-header">
              <strong>{{ group.display_name }}</strong>
              <el-tag :type="group.source === 'layout_inferred' ? 'warning' : group.source === 'unknown' ? 'info' : 'success'">
                {{ group.source === 'layout_inferred' ? '推测牙位' : group.source === 'unknown' ? '局部区域' : '模型牙位' }}
              </el-tag>
            </div>
            <p
              v-for="item in group.findings"
              :key="`${group.display_name}-${item.finding_label}-${item.confidence}`"
              class="clinical-copy"
            >
              {{ item.finding_label }}：{{ item.clinical_meaning }} 建议：{{ item.recommendation }}
            </p>
            <p
              v-for="item in group.findings.filter((entry) => entry.follow_up_exam.length > 0)"
              :key="`${group.display_name}-${item.finding_label}-exam`"
              class="clinical-copy"
            >
              建议补充检查：{{ item.follow_up_exam.join('、') }}
            </p>
          </div>
        </div>
      </article>

      <div class="report-box compact-report-meta">
        <div class="panel-header">
          <span>病例要点</span>
          <el-tag type="success">{{ currentRecord.detections.length }} 个病灶</el-tag>
        </div>
        <div class="report-meta-strip">
          <span>{{ currentRecord.patient?.name ?? currentRecord.patient_id }}</span>
          <span>{{ currentRecord.filename }}</span>
          <span>{{ currentRecord.report.status === 'finalized' ? '已归档' : '待完成' }}</span>
        </div>
      </div>

      <div class="report-box">
        <div class="panel-header">
          <span>医生意见</span>
          <el-tag type="success">{{ reviewTextLength }} 字</el-tag>
        </div>
        <el-input
          v-model="reviewText"
          type="textarea"
          :rows="6"
          placeholder="例如：AI诊断基本准确，建议补充根尖片确认根尖状态"
        />
      </div>
      <div class="actions report-action-bar">
        <el-button type="primary" :disabled="!canSubmit" @click="emit('submit')">保存审核意见</el-button>
        <el-button type="success" :disabled="!canFinalize" @click="emit('finalize')">确认为正式报告</el-button>
        <el-button :disabled="!currentRecord" @click="revisionDrawerVisible = true">版本记录</el-button>
        <el-button :disabled="!currentRecord" @click="handlePrintReport">打印预览</el-button>
        <el-button :disabled="!currentRecord" @click="handleExportHtml">下载 PDF 报告</el-button>
      </div>
    </template>
  </el-card>

  <ReportRevisionDrawer
    v-model:visible="revisionDrawerVisible"
    :report-id="currentRecord?.report.report_id ?? null"
  />
</template>
