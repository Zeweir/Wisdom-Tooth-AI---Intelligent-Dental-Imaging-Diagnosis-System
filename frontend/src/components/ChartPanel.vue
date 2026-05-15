<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'

use([CanvasRenderer, PieChart, BarChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const props = defineProps<{
  option: Record<string, unknown>
  height?: string
  loading?: boolean
}>()

const chartHeight = computed(() => props.height ?? '300px')
</script>

<template>
  <div class="chart-panel" :style="{ height: chartHeight }">
    <VChart :option="option" autoresize :loading="loading" />
  </div>
</template>

<style scoped>
.chart-panel {
  width: 100%;
  min-height: 200px;
}
</style>
