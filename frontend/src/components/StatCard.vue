<script setup lang="ts">
const props = defineProps<{
  label: string
  value: string | number
  description?: string
}>()
</script>

<template>
  <article class="stat-card-v2">
    <div class="stat-card-value">{{ props.value }}</div>
    <div class="stat-card-label">{{ props.label }}</div>
    <p v-if="props.description" class="stat-card-desc">{{ props.description }}</p>
  </article>
</template>
