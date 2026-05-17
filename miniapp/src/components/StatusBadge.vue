<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const config = computed(() => {
  const map: Record<string, { text: string; bg: string; color: string }> = {
    processing: { text: '处理中', bg: '#fef3c7', color: '#d97706' },
    ai_generated: { text: '待审核', bg: '#dbeafe', color: '#2563eb' },
    doctor_reviewed: { text: '已审核', bg: '#d1fae5', color: '#059669' },
    finalized: { text: '已归档', bg: '#f3f4f6', color: '#6b7280' },
    failed: { text: '失败', bg: '#fee2e2', color: '#dc2626' },
  }
  return map[props.status] ?? { text: props.status, bg: '#f3f4f6', color: '#6b7280' }
})
</script>

<template>
  <text
    class="sb-badge"
    :style="'background:' + config.bg + ';color:' + config.color"
  >{{ config.text }}</text>
</template>

<style>
.sb-badge {
  display: inline-block;
  font-size: 22px;
  padding: 4px 14px;
  border-radius: 20px;
  font-weight: 500;
  flex-shrink: 0;
}
</style>
