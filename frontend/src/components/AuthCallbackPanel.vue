<script setup lang="ts">
import { useHandleSignInCallback } from '@logto/vue'

useHandleSignInCallback(() => {
  window.location.replace('/')
})
</script>

<template>
  <div class="page-shell">
    <el-card class="panel" shadow="never">
      <el-result icon="info" title="正在完成登录" sub-title="请稍候，系统正在处理 Logto 登录回调。" />
    </el-card>
  </div>
</template>
