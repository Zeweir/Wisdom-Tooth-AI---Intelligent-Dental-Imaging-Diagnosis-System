<script setup lang="ts">
import { onMounted, provide } from 'vue'
import { useAuth } from './composables/useAuth'
import { useWorkbench } from './composables/useWorkbench'
import { workbenchKey } from './workbench'

const auth = useAuth()
const workbench = useWorkbench()
provide(workbenchKey, workbench)

onMounted(async () => {
  await auth.refreshAuthState()
})
</script>

<template>
  <RouterView />
</template>
