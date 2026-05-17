<script setup lang="ts">
defineProps<{
  icon?: string
  text?: string
  subText?: string
}>()
</script>

<template>
  <view class="es-wrap">
    <text class="es-icon" v-if="icon">{{ icon }}</text>
    <text class="es-text" v-if="text">{{ text }}</text>
    <text class="es-sub" v-if="subText">{{ subText }}</text>
    <slot />
  </view>
</template>

<style>
.es-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 160px 48px 0;
}
.es-icon {
  font-size: 100px;
  margin-bottom: 24px;
}
.es-text {
  font-size: 30px;
  font-weight: 600;
  color: #1e293b;
  text-align: center;
  display: block;
}
.es-sub {
  font-size: 26px;
  color: #94a3b8;
  margin-top: 8px;
  text-align: center;
  display: block;
}
</style>
