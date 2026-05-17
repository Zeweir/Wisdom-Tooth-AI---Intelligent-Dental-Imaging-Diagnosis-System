<script setup lang="ts">
import Taro from '@tarojs/taro'

defineProps<{ current: number }>()

const tabs = [
  { path: '/pages/index/index', text: '首页', icon: 'tooth-icon-home' },
  { path: '/pages/history/history', text: '记录', icon: 'tooth-icon-list' },
  { path: '/pages/me/me', text: '我的', icon: 'tooth-icon-user' },
]

function switchTab(path: string) {
  Taro.switchTab({ url: path })
}
</script>

<template>
  <view class="ctb-root">
    <view class="ctb-bar">
      <view
        v-for="(tab, idx) in tabs"
        :key="tab.path"
        class="ctb-item"
        :class="{ 'ctb-item-on': current === idx }"
        @tap="switchTab(tab.path)"
      >
        <!-- Home icon -->
        <view class="ctb-icon" v-if="idx === 0">
          <view class="ctb-home-shape" :class="{ 'ctb-home-on': current === 0 }">
            <view class="ctb-home-roof" />
            <view class="ctb-home-body" />
            <view class="ctb-home-door" />
          </view>
        </view>

        <!-- List icon -->
        <view class="ctb-icon" v-if="idx === 1">
          <view class="ctb-list-shape" :class="{ 'ctb-list-on': current === 1 }">
            <view class="ctb-list-line" v-for="l in 3" :key="l" />
          </view>
        </view>

        <!-- User icon -->
        <view class="ctb-icon" v-if="idx === 2">
          <view class="ctb-user-shape" :class="{ 'ctb-user-on': current === 2 }">
            <view class="ctb-user-head" />
            <view class="ctb-user-body" />
          </view>
        </view>

        <text class="ctb-label">{{ tab.text }}</text>

        <!-- Active indicator dot -->
        <view class="ctb-dot" v-if="current === idx" />
      </view>
    </view>
    <view class="ctb-safe" />
  </view>
</template>

<style>
.ctb-root {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 9999;
}

.ctb-bar {
  display: flex;
  flex-direction: row;
  background: #fff;
  border-top: 1px solid #f1f5f9;
  height: 96px;
}

.ctb-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.ctb-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2px;
}

.ctb-label {
  font-size: 20px;
  color: #999;
  line-height: 1;
  margin-top: 2px;
}

.ctb-item-on .ctb-label {
  color: #5b5fe3;
  font-weight: 600;
}

.ctb-dot {
  position: absolute;
  top: 8px;
  width: 6px;
  height: 6px;
  border-radius: 3px;
  background: #5b5fe3;
}

/* Home icon */
.ctb-home-shape {
  position: relative;
  width: 28px;
  height: 24px;
}
.ctb-home-roof {
  width: 0;
  height: 0;
  border-left: 14px solid transparent;
  border-right: 14px solid transparent;
  border-bottom: 8px solid #999;
  margin: 0 auto;
}
.ctb-home-body {
  width: 18px;
  height: 12px;
  background: #999;
  margin: 0 auto;
  border-radius: 0 0 2px 2px;
}
.ctb-home-door {
  width: 6px;
  height: 8px;
  background: #fff;
  margin: -12px auto 0;
  border-radius: 2px 2px 0 0;
}
.ctb-home-on .ctb-home-roof { border-bottom-color: #5b5fe3; }
.ctb-home-on .ctb-home-body { background: #5b5fe3; }

/* List icon */
.ctb-list-shape {
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: 22px;
  height: 24px;
}
.ctb-list-line {
  height: 3px;
  background: #999;
  border-radius: 2px;
  margin-bottom: 4px;
}
.ctb-list-line:first-child { width: 100%; }
.ctb-list-line:nth-child(2) { width: 70%; }
.ctb-list-line:last-child { width: 85%; margin-bottom: 0; }
.ctb-list-on .ctb-list-line { background: #5b5fe3; }

/* User icon */
.ctb-user-shape {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 28px;
  height: 24px;
}
.ctb-user-head {
  width: 14px;
  height: 14px;
  border: 3px solid #999;
  border-radius: 7px;
}
.ctb-user-body {
  width: 20px;
  height: 10px;
  background: #999;
  border-radius: 10px 10px 0 0;
  margin-top: 2px;
}
.ctb-user-on .ctb-user-head { border-color: #5b5fe3; }
.ctb-user-on .ctb-user-body { background: #5b5fe3; }

/* Safe area */
.ctb-safe {
  height: constant(safe-area-inset-bottom);
  height: env(safe-area-inset-bottom);
  background: #fff;
}
</style>
