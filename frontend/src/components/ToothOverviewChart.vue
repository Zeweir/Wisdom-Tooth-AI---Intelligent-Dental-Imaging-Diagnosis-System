<script setup lang="ts">
import { computed } from 'vue'

import type { ToothFindingGroup } from '../types/analysis'

const props = defineProps<{
  toothFindings: ToothFindingGroup[]
  selectedToothKey?: string | null
}>()
const emit = defineEmits<{
  select: [toothKey: string | null]
}>()

const upperArch = ['18', '17', '16', '15', '14', '13', '12', '11', '21', '22', '23', '24', '25', '26', '27', '28']
const lowerArch = ['48', '47', '46', '45', '44', '43', '42', '41', '31', '32', '33', '34', '35', '36', '37', '38']

function resolveRiskType(group: ToothFindingGroup) {
  const severities = group.findings.map((item) => item.severity)
  if (severities.some((item) => item.includes('高') || item.toLowerCase().includes('high'))) {
    return 'danger'
  }
  if (severities.some((item) => item.includes('中') || item.toLowerCase().includes('medium'))) {
    return 'warning'
  }
  return 'success'
}

const toothMap = computed(() => {
  const map = new Map<string, ToothFindingGroup & { riskType: 'danger' | 'warning' | 'success' }>()
  for (const group of props.toothFindings) {
    if (!/^\d{2}$/.test(group.tooth_id)) {
      continue
    }
    map.set(group.tooth_id, {
      ...group,
      riskType: resolveRiskType(group),
    })
  }
  return map
})

const nonFdiFindings = computed(() =>
  props.toothFindings.filter((group) => !/^\d{2}$/.test(group.tooth_id))
)

function describeTooth(group?: ToothFindingGroup) {
  if (!group) {
    return '未检出明确问题'
  }
  const summary = group.findings.map((item) => item.finding_label).join('、')
  const source = group.source === 'layout_inferred' ? '推测牙位' : group.source === 'unknown' ? '局部区域' : '模型牙位'
  return `${source}：${summary}`
}

function handleSelect(toothKey: string, hasFinding: boolean) {
  if (!hasFinding) {
    return
  }
  emit('select', props.selectedToothKey === toothKey ? null : toothKey)
}
</script>

<template>
  <section class="tooth-overview diagnosis-finding-card">
    <div class="panel-header">
      <span>牙位总览图</span>
      <div class="tooth-overview-legend">
        <span class="is-success">低风险</span>
        <span class="is-warning">中风险</span>
        <span class="is-danger">高风险</span>
      </div>
    </div>

    <div class="tooth-arch tooth-arch-upper">
      <button
        v-for="tooth in upperArch"
        :key="tooth"
        type="button"
        class="tooth-cell"
        :class="[
          {
            'is-active': toothMap.has(tooth),
            'is-selected': props.selectedToothKey === tooth,
            'is-success': toothMap.get(tooth)?.riskType === 'success',
            'is-warning': toothMap.get(tooth)?.riskType === 'warning',
            'is-danger': toothMap.get(tooth)?.riskType === 'danger',
            'is-inferred': toothMap.get(tooth)?.source === 'layout_inferred',
          },
        ]"
        :title="describeTooth(toothMap.get(tooth))"
        @click="handleSelect(tooth, toothMap.has(tooth))"
      >
        <strong>{{ tooth }}</strong>
        <small>{{ toothMap.get(tooth)?.findings[0]?.finding_label || '正常' }}</small>
      </button>
    </div>

    <div class="tooth-arch-divider">咬合面</div>

    <div class="tooth-arch tooth-arch-lower">
      <button
        v-for="tooth in lowerArch"
        :key="tooth"
        type="button"
        class="tooth-cell"
        :class="[
          {
            'is-active': toothMap.has(tooth),
            'is-selected': props.selectedToothKey === tooth,
            'is-success': toothMap.get(tooth)?.riskType === 'success',
            'is-warning': toothMap.get(tooth)?.riskType === 'warning',
            'is-danger': toothMap.get(tooth)?.riskType === 'danger',
            'is-inferred': toothMap.get(tooth)?.source === 'layout_inferred',
          },
        ]"
        :title="describeTooth(toothMap.get(tooth))"
        @click="handleSelect(tooth, toothMap.has(tooth))"
      >
        <strong>{{ tooth }}</strong>
        <small>{{ toothMap.get(tooth)?.findings[0]?.finding_label || '正常' }}</small>
      </button>
    </div>

    <div v-if="nonFdiFindings.length > 0" class="tooth-overview-extras">
      <div class="sub-title">局部区域或 ROI</div>
      <div class="tag-wrap">
        <el-tag
          v-for="group in nonFdiFindings"
          :key="`${group.display_name}-${group.source}`"
          :type="group.source === 'unknown' ? 'info' : 'warning'"
          :effect="props.selectedToothKey === group.display_name ? 'dark' : 'light'"
          @click="emit('select', props.selectedToothKey === group.display_name ? null : group.display_name)"
        >
          {{ group.display_name }}：{{ group.findings.map((item) => item.finding_label).join('、') }}
        </el-tag>
      </div>
    </div>
  </section>
</template>
