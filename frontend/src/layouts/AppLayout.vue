<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import AppHeader from '../components/AppHeader.vue'
import AppSidebar from '../components/AppSidebar.vue'

const route = useRoute()
const sidebarCollapsed = ref(false)

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const routeTransitionName = computed(() => {
  const motion = route.meta?.motion
  if (motion === 'none') {
    return ''
  }
  return 'route-fade'
})
</script>

<template>
  <div class="app-layout" :class="{ 'is-collapsed': sidebarCollapsed }">
    <aside class="app-layout-sidebar">
      <AppSidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    </aside>

    <div class="app-layout-main">
      <AppHeader />

      <main class="app-layout-content">
        <RouterView v-slot="{ Component }">
          <Transition :name="routeTransitionName" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </Transition>
        </RouterView>
      </main>

      <footer class="app-layout-footer">
        © 2025 智齿 AI 牙齿影像智能诊断系统
      </footer>
    </div>
  </div>
</template>
