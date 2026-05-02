<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const statusMap: Record<string, { text: string; type: 'success' | 'warning' | 'info' | 'danger' }> = {
  processing: { text: '诊断中', type: 'info' },
  ai_generated: { text: '待审核', type: 'warning' },
  doctor_reviewed: { text: '待确认', type: 'warning' },
  finalized: { text: '已完成', type: 'success' },
  completed: { text: '已完成', type: 'success' },
  exception: { text: '异常', type: 'danger' },
}

const display = computed(() => statusMap[props.status] ?? { text: props.status, type: 'info' as const })
</script>

<template>
  <el-tag :type="display.type" effect="light">{{ display.text }}</el-tag>
</template>
