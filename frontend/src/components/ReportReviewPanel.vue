<script setup lang="ts">
import { computed } from 'vue'
import type { AnalysisItem } from '../types/analysis'

const props = defineProps<{
  currentRecord: AnalysisItem | null
  canReview: boolean
  canFinalizeReport: boolean
}>()

const reviewText = defineModel<string>('reviewText', { required: true })
const canSubmit = computed(() => Boolean(props.currentRecord) && props.canReview)
const canFinalize = computed(() => props.currentRecord?.report.status === 'doctor_reviewed' && props.canFinalizeReport)

const emit = defineEmits<{
  submit: []
  finalize: []
}>()
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
      <div class="report-box">
        <div class="sub-title">AI 生成报告</div>
        <p>{{ currentRecord.report.content }}</p>
      </div>
      <div class="report-box">
        <div class="sub-title">当前报告状态</div>
        <el-tag :type="currentRecord.report.status === 'finalized' ? 'success' : 'warning'">
          {{ currentRecord.report.status }}
        </el-tag>
      </div>
      <div class="report-box">
        <div class="sub-title">医生审核意见</div>
        <el-input
          v-model="reviewText"
          type="textarea"
          :rows="6"
          placeholder="例如：AI诊断基本准确，建议补充根尖片确认根尖状态"
        />
      </div>
      <div class="actions">
        <el-button type="primary" :disabled="!canSubmit" @click="emit('submit')">提交审核</el-button>
        <el-button type="success" :disabled="!canFinalize" @click="emit('finalize')">正式确认</el-button>
      </div>
    </template>
  </el-card>
</template>
