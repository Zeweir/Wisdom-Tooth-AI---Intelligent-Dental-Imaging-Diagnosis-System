<script setup lang="ts">
import { provide } from 'vue'

import { useWorkbench } from './composables/useWorkbench'
import { workbenchKey } from './workbench'

const workbench = useWorkbench()
provide(workbenchKey, workbench)
</script>

<template>
  <RouterView />
</template>
