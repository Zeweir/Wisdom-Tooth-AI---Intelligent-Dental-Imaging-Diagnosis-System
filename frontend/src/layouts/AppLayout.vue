<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import AppHeader from '../components/AppHeader.vue'
import AppSidebar from '../components/AppSidebar.vue'

const route = useRoute()
const sidebarCollapsed = ref(false)

const breadcrumbItems = computed(() => {
  return route.matched
    .filter((item) => item.meta?.title)
    .map((item) => ({
      path: item.path,
      title: String(item.meta?.title ?? ''),
    }))
})

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="app-layout" :class="{ 'is-collapsed': sidebarCollapsed }">
    <aside class="app-layout-sidebar">
      <AppSidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    </aside>

    <div class="app-layout-main">
      <AppHeader />

      <section class="app-layout-breadcrumb">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item
            v-for="(item, index) in breadcrumbItems"
            :key="`${item.path}-${index}`"
          >
            <RouterLink v-if="index < breadcrumbItems.length - 1" :to="item.path">{{ item.title }}</RouterLink>
            <span v-else>{{ item.title }}</span>
          </el-breadcrumb-item>
        </el-breadcrumb>
      </section>

      <main class="app-layout-content">
        <RouterView />
      </main>

      <footer class="app-layout-footer">
        © 2025 智齿 AI 牙齿影像智能诊断系统
      </footer>
    </div>
  </div>
</template>
