<script setup lang="ts">
import type { AnalysisItem } from '../types/analysis'
import { downloadClinicalReport, printClinicalReport } from '../utils/report'
import ToothOverviewChart from './ToothOverviewChart.vue'

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
      <span>PDF：{{ props.record.report.pdf_variant || '未生成' }}</span>
    </div>
    <article class="report-box">
      <div class="sub-title">AI 诊断摘要</div>
      <p class="clinical-copy">{{ props.record.report.structured_content.summary || props.record.report.content || '暂无 AI 诊断内容' }}</p>
    </article>
    <article v-if="props.record.report.structured_content.key_findings.length > 0" class="report-box">
      <div class="sub-title">关键发现</div>
      <div class="report-preview-points">
        <p v-for="item in props.record.report.structured_content.key_findings" :key="item" class="clinical-copy">{{ item }}</p>
      </div>
    </article>
    <article v-if="props.record.report.structured_content.follow_up_plan.length > 0" class="report-box">
      <div class="sub-title">建议处理</div>
      <div class="report-preview-points">
        <p v-for="item in props.record.report.structured_content.follow_up_plan" :key="item" class="clinical-copy">{{ item }}</p>
      </div>
    </article>
    <article v-if="props.record.report.structured_content.tooth_findings.length > 0" class="report-box">
      <div class="sub-title">按牙位问题说明</div>
      <ToothOverviewChart :tooth-findings="props.record.report.structured_content.tooth_findings" />
      <div class="report-preview-points">
        <div v-for="group in props.record.report.structured_content.tooth_findings" :key="`${group.display_name}-${group.source}`" class="report-tooth-group">
          <div class="panel-header">
            <strong>{{ group.display_name }}</strong>
            <el-tag :type="group.source === 'layout_inferred' ? 'warning' : group.source === 'unknown' ? 'info' : 'success'">
              {{ group.source === 'layout_inferred' ? '推测牙位' : group.source === 'unknown' ? '局部区域' : '模型牙位' }}
            </el-tag>
          </div>
          <p v-for="item in group.findings" :key="`${group.display_name}-${item.finding_label}`" class="clinical-copy">
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
    <article class="report-box">
      <div class="sub-title">医生审核意见</div>
      <p class="clinical-copy">{{ props.record.report.doctor_review || '暂无医生审核意见' }}</p>
    </article>
    <div class="report-preview-actions">
      <el-button type="primary" @click="downloadClinicalReport(props.record)">下载 PDF 报告</el-button>
      <el-button @click="printClinicalReport(props.record)">打印预览</el-button>
    </div>
  </div>
</template>
