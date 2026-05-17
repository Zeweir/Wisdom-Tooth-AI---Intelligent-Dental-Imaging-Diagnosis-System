<script setup lang="ts">
defineProps<{ lines?: number }>()
</script>

<template>
  <view class="sk-card">
    <view class="sk-line sk-title" />
    <view v-for="i in (lines ?? 2)" :key="i" class="sk-line" :style="'width:' + (90 - (i - 1) * 15) + '%'" />
  </view>
</template>

<style>
.sk-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px 24px;
}
.sk-line {
  height: 20px;
  background: #e2e8f0;
  border-radius: 4px;
  margin-bottom: 14px;
}
.sk-title {
  width: 45%;
  height: 24px;
  margin-bottom: 20px;
}
</style>
