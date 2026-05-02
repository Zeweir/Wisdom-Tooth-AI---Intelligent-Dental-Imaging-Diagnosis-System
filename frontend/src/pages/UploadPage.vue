<script setup lang="ts">
import { computed, onMounted } from 'vue'

import PageHeader from '../components/PageHeader.vue'
import UploadPanel from '../components/UploadPanel.vue'
import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()
const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const canUpload = workbench.canUpload
const canReadImages = workbench.canReadImages
const loading = workbench.loading
const socketEvents = workbench.socketEvents
const currentRecord = workbench.currentRecord
const handleUpload = workbench.handleUpload
const fetchRecords = workbench.fetchRecords
const beginSignOut = workbench.beginSignOut

const latestRecord = computed(() => currentRecord.value ?? workbench.records.value[0] ?? null)

onMounted(async () => {
  if (canReadImages.value) {
    await fetchRecords()
  }
})
</script>

<template>
  <div class="page-stack">
    <PageHeader
      title="影像上传"
      description="上传牙齿影像后将自动触发 AI 分析，并生成可审核的诊断草稿。"
    >
      <template #actions>
        <RouterLink v-if="latestRecord" :to="{ path: '/workspace', query: { image_id: latestRecord.image_id } }" class="el-button el-button--primary is-plain">
          <span>查看最新诊断</span>
        </RouterLink>
      </template>
    </PageHeader>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !canUpload"
      title="当前账号暂无影像上传权限"
      description="上传影像需要 `upload:images` 权限，请为当前用户分配 radiologist 或包含该权限的角色。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <section v-else class="upload-page-grid">
      <UploadPanel
        v-model:loading="loading"
        v-model:socket-events="socketEvents"
        :can-upload="canUpload"
        @submit="handleUpload"
      />

      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>上传后信息</span>
            <el-tag type="info">实时更新</el-tag>
          </div>
        </template>
        <el-empty v-if="!latestRecord" description="上传后可在此查看影像与诊断入口" />
        <div v-else class="upload-page-latest">
          <div class="upload-meta-grid">
            <span>患者：{{ latestRecord.patient?.name ?? latestRecord.patient_id }}</span>
            <span>影像文件：{{ latestRecord.filename }}</span>
            <span>上传时间：{{ new Date(latestRecord.created_at).toLocaleString() }}</span>
            <span>诊断状态：{{ latestRecord.report.status }}</span>
          </div>
          <RouterLink :to="{ path: '/workspace', query: { image_id: latestRecord.image_id } }" class="el-button el-button--primary">
            <span>进入 AI 诊断</span>
          </RouterLink>
        </div>
      </el-card>
    </section>
  </div>
</template>
