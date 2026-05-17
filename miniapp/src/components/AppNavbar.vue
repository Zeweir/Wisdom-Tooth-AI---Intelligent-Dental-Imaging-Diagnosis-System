<script setup lang="ts">
import Taro from '@tarojs/taro'

defineProps<{ title?: string; transparent?: boolean }>()

const info = Taro.getWindowInfo?.() || { statusBarHeight: 20 }
const statusBarHeight = info.statusBarHeight ?? 20
const navHeight = 44
const totalHeight = statusBarHeight + navHeight
</script>

<template>
  <view
    class="an-wrap"
    :class="{ 'an-transparent': transparent }"
    :style="'padding-top:' + statusBarHeight + 'px;height:' + totalHeight + 'px'"
  >
    <view class="an-content">
      <slot name="left" />
      <text class="an-title" v-if="title && !$slots.center">{{ title }}</text>
      <slot name="center" />
      <slot name="right" />
    </view>
  </view>
  <view :style="'height:' + totalHeight + 'px'" v-if="!transparent" />
</template>

<style>
.an-wrap {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: #fff;
}
.an-transparent { background: transparent; }
.an-content {
  height: 44px;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  position: relative;
}
.an-title {
  font-size: 17px;
  font-weight: 600;
  color: #1e293b;
}
</style>
