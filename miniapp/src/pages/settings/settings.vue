<script setup lang="ts">
import { ref } from 'vue'
import Taro from '@tarojs/taro'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()

interface CacheInfo {
  used: string
  limit: string
  percent: number
  files: number
}

const cacheInfo = ref<CacheInfo>({ used: '32.5 MB', limit: '200 MB', percent: 16, files: 48 })
const showCacheModal = ref(false)
const clearing = ref(false)

function getStorageUsage() {
  try {
    const info = Taro.getStorageInfoSync()
    cacheInfo.value = {
      used: (info.currentSize / 1024).toFixed(1) + ' MB',
      limit: (info.limitSize / 1024).toFixed(0) + ' MB',
      percent: Math.round((info.currentSize / info.limitSize) * 100),
      files: info.keys.length,
    }
  } catch { /* use default */ }
}

Taro.nextTick(getStorageUsage)

function clearCache() {
  clearing.value = true
  setTimeout(() => {
    try {
      // Keep auth data, clear rest
      const token = Taro.getStorageSync('access_token')
      const user = Taro.getStorageSync('user')
      Taro.clearStorageSync()
      if (token) Taro.setStorageSync('access_token', token)
      if (user) Taro.setStorageSync('user', user)
      showCacheModal.value = false
      getStorageUsage()
      Taro.showToast({ title: '缓存已清除', icon: 'success' })
    } catch {
      Taro.showToast({ title: '清除失败', icon: 'error' })
    }
    clearing.value = false
  }, 600)
}

const settingsGroups = [
  {
    title: '存储',
    items: [
      {
        icon: '🗂',
        text: '清除缓存',
        sub: '清理临时图片和页面缓存，保留登录信息',
        action: () => { showCacheModal.value = true },
        extra: `${cacheInfo.value.used} 已用 / ${cacheInfo.value.files} 个文件`,
      },
    ],
  },
  {
    title: '账号',
    items: [
      {
        icon: '🔑',
        text: '修改密码',
        sub: '联系管理员修改登录密码',
        action: () => Taro.showToast({ title: '请联系系统管理员', icon: 'none' }),
      },
      {
        icon: '🛡',
        text: '账号安全',
        sub: `当前角色: ${auth.user?.role_label || '未知'} · JWT 鉴权保护`,
        action: () => Taro.navigateTo({ url: '/pages/about/about' }),
      },
    ],
  },
  {
    title: '其他',
    items: [
      {
        icon: '📖',
        text: '使用帮助',
        sub: '了解如何使用智齿 AI 的各项功能',
        action: () => Taro.navigateTo({ url: '/pages/help/help' }),
      },
      {
        icon: 'ℹ️',
        text: '关于智齿 AI',
        sub: '版本信息、技术栈和团队介绍',
        action: () => Taro.navigateTo({ url: '/pages/about/about' }),
      },
    ],
  },
]
</script>

<template>
  <view class="se-page">
    <!-- Header -->
    <view class="se-header">
      <text class="se-title">设置</text>
    </view>

    <!-- Storage Card -->
    <view class="se-storage-card">
      <view class="se-storage-head">
        <text class="se-storage-title">存储空间</text>
        <text class="se-storage-pct">{{ cacheInfo.percent }}%</text>
      </view>
      <view class="se-storage-bar">
        <view class="se-storage-fill" :style="{ width: cacheInfo.percent + '%' }" />
      </view>
      <text class="se-storage-meta">{{ cacheInfo.used }} / {{ cacheInfo.limit }}</text>
    </view>

    <!-- Settings Groups -->
    <view v-for="g in settingsGroups" :key="g.title" class="se-group">
      <text class="se-group-title">{{ g.title }}</text>
      <view class="se-group-list">
        <view
          v-for="item in g.items" :key="item.text"
          class="se-item"
          @tap="item.action"
        >
          <view class="se-item-left">
            <text class="se-item-icon">{{ item.icon }}</text>
            <view class="se-item-info">
              <text class="se-item-text">{{ item.text }}</text>
              <text class="se-item-sub">{{ item.sub }}</text>
            </view>
          </view>
          <view class="se-item-right">
            <text class="se-item-extra" v-if="item.extra">{{ item.extra }}</text>
            <text class="se-item-arrow">›</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Cache Modal -->
    <view v-if="showCacheModal" class="se-overlay" @tap="showCacheModal = false">
      <view class="se-modal" @tap.stop>
        <text class="se-modal-title">清除缓存</text>
        <text class="se-modal-desc">将清除临时图片缓存和页面数据，保留登录账号信息。确定继续？</text>
        <view class="se-modal-btns">
          <button class="se-modal-cancel" @tap="showCacheModal = false">取消</button>
          <button class="se-modal-confirm" :loading="clearing" @tap="clearCache">确定清除</button>
        </view>
      </view>
    </view>
  </view>
</template>

<style>
/* === Settings Page === */
.se-page { min-height: 100vh; padding-bottom: 48px; }

.se-header { padding: 24px 28px 16px; }
.se-title { font-size: 38px; font-weight: 800; color: #1e293b; }

/* Storage Card */
.se-storage-card {
  margin: 8px 28px 24px; padding: 24px;
  background: #fff; border-radius: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.se-storage-head {
  display: flex; flex-direction: row; align-items: center;
  justify-content: space-between; margin-bottom: 14px;
}
.se-storage-title { font-size: 28px; font-weight: 600; color: #1e293b; }
.se-storage-pct { font-size: 28px; font-weight: 700; color: #5b5fe3; }
.se-storage-bar { height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; margin-bottom: 10px; }
.se-storage-fill { height: 8px; background: linear-gradient(90deg, #5b5fe3, #818cf8); border-radius: 4px; }
.se-storage-meta { font-size: 22px; color: #94a3b8; display: block; }

/* Groups */
.se-group { margin: 0 28px 8px; }
.se-group-title { display: block; font-size: 24px; color: #94a3b8; padding: 16px 4px 12px; }
.se-group-list { background: #fff; border-radius: 20px; overflow: hidden; }
.se-item {
  display: flex; flex-direction: row; align-items: center;
  justify-content: space-between; padding: 24px 20px;
  border-bottom: 1px solid #f8fafc;
}
.se-item:last-child { border-bottom: 0; }
.se-item-left { display: flex; flex-direction: row; align-items: center; flex: 1; min-width: 0; }
.se-item-icon { font-size: 28px; width: 44px; text-align: center; margin-right: 14px; flex-shrink: 0; }
.se-item-info { flex: 1; min-width: 0; }
.se-item-text { display: block; font-size: 28px; color: #1e293b; font-weight: 500; }
.se-item-sub { display: block; font-size: 22px; color: #94a3b8; margin-top: 4px; }
.se-item-right { display: flex; flex-direction: row; align-items: center; flex-shrink: 0; }
.se-item-extra { font-size: 22px; color: #cbd5e1; margin-right: 8px; }
.se-item-arrow { font-size: 28px; color: #cbd5e1; }

/* Modal */
.se-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 999; }
.se-modal { width: 560px; background: #fff; border-radius: 24px; padding: 40px 32px 28px; }
.se-modal-title { font-size: 34px; font-weight: 700; color: #1e293b; display: block; text-align: center; }
.se-modal-desc { font-size: 26px; color: #64748b; display: block; text-align: center; margin-top: 12px; line-height: 1.6; }
.se-modal-btns { display: flex; flex-direction: row; margin-top: 28px; }
.se-modal-cancel { flex: 1; height: 84px; line-height: 84px; text-align: center; background: #f1f5f9; color: #475569; border-radius: 14px; font-size: 28px; font-weight: 500; border: none; margin-right: 14px; }
.se-modal-confirm { flex: 1; height: 84px; line-height: 84px; text-align: center; background: #ef4444; color: #fff; border-radius: 14px; font-size: 28px; font-weight: 600; border: none; }
</style>
