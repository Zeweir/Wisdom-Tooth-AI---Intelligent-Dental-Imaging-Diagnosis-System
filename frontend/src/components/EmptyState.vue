<script setup lang="ts">
const props = defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="empty-state">
    <strong>{{ props.title }}</strong>
    <p v-if="props.description">{{ props.description }}</p>
    <div class="empty-state-actions">
      <slot name="actions" />
    </div>
  </div>
</template>
