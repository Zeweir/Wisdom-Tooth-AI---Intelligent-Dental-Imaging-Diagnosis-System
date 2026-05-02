<script setup lang="ts">
const props = defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <section class="page-header">
    <div>
      <h2>{{ props.title }}</h2>
      <p v-if="props.description">{{ props.description }}</p>
    </div>
    <div class="page-header-actions">
      <slot name="actions" />
    </div>
  </section>
</template>
