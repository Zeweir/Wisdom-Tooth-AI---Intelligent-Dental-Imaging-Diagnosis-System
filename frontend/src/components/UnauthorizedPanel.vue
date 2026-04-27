<script setup lang="ts">
const props = defineProps<{
  title: string
  description: string
}>()
</script>

<template>
  <el-card class="panel" shadow="never">
    <el-result icon="warning" :title="props.title" :sub-title="props.description">
      <template #extra>
        <slot />
      </template>
    </el-result>
  </el-card>
</template>
