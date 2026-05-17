<script setup lang="ts">
import { ref } from 'vue'
import Taro, { useDidShow, usePullDownRefresh } from '@tarojs/taro'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()

interface Notification {
  id: string
  type: 'analysis_done' | 'report_reviewed' | 'report_finalized' | 'system'
  title: string
  content: string
  time: string
  read: boolean
  imageId?: string
}

const list = ref<Notification[]>([
  {
    id: '1', type: 'report_finalized',
    title: '报告已归档',
    content: '患者 P-0001 的全景片诊断报告已由主任医生正式确认并归档。',
    time: '2026-05-17 10:32', read: false, imageId: 'img-001',
  },
  {
    id: '2', type: 'report_reviewed',
    title: '报告已审核',
    content: '患者 P-0002 的根尖片诊断报告已通过审核医生复核。',
    time: '2026-05-17 09:15', read: false, imageId: 'img-002',
  },
  {
    id: '3', type: 'analysis_done',
    title: 'AI 分析完成',
    content: '患者 P-0003 的全景片已完成 AI 检测，检测到 2 处疑似病灶，请尽快审核。',
    time: '2026-05-16 18:42', read: true,
  },
  {
    id: '4', type: 'system',
    title: '系统更新通知',
    content: '智齿 AI 已升级至 v0.1.0，新增症状自测、数据集管理、报告版本快照等功能。',
    time: '2026-05-16 12:00', read: true,
  },
  {
    id: '5', type: 'analysis_done',
    title: 'AI 分析完成',
    content: '患者 P-0004 的 CBCT 影像已完成 AI 检测，检测到 1 处疑似病灶。',
    time: '2026-05-15 15:20', read: true,
  },
  {
    id: '6', type: 'report_reviewed',
    title: '报告已审核',
    content: '患者 P-0005 的全景片诊断报告已通过审核医生复核，等待主任医生确认。',
    time: '2026-05-15 11:08', read: true,
  },
])

const unreadCount = ref(2)

useDidShow(async () => {
  await auth.init()
})

usePullDownRefresh(async () => {
  await new Promise(r => setTimeout(r, 800))
  Taro.stopPullDownRefresh()
  Taro.showToast({ title: '已刷新', icon: 'success', duration: 1500 })
})

function getTypeIcon(type: string) {
  const map: Record<string, string> = {
    analysis_done: '🤖',
    report_reviewed: '✅',
    report_finalized: '📁',
    system: '📢',
  }
  return map[type] || '📌'
}

function getTypeBg(type: string) {
  const map: Record<string, string> = {
    analysis_done: '#eff6ff',
    report_reviewed: '#ecfdf5',
    report_finalized: '#f3f4f6',
    system: '#fefce8',
  }
  return map[type] || '#f8fafc'
}

function getTypeBorder(type: string) {
  const map: Record<string, string> = {
    analysis_done: '#3b82f6',
    report_reviewed: '#10b981',
    report_finalized: '#6b7280',
    system: '#eab308',
  }
  return map[type] || '#e2e8f0'
}

function markAsRead(item: Notification) {
  if (!item.read) {
    item.read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
}

function goDetail(imageId?: string) {
  if (imageId) {
    Taro.navigateTo({ url: `/pages/result/result?imageId=${imageId}` })
  }
}

function markAllRead() {
  list.value.forEach(n => { n.read = true })
  unreadCount.value = 0
  Taro.showToast({ title: '全部已读', icon: 'success', duration: 1500 })
}
</script>

<template>
  <view class="nf-page">
    <!-- Header -->
    <view class="nf-header">
      <text class="nf-title">消息通知</text>
      <view class="nf-header-right" v-if="unreadCount > 0">
        <text class="nf-unread">{{ unreadCount }} 条未读</text>
        <text class="nf-mark-all" @tap="markAllRead">全部已读</text>
      </view>
      <text class="nf-all-read" v-else>全部已读 ✓</text>
    </view>

    <!-- Not Logged In -->
    <view v-if="!auth.isLoggedIn && auth.ready" class="nf-empty">
      <text class="nf-empty-icon">🔔</text>
      <text class="nf-empty-text">登录后查看消息通知</text>
    </view>

    <!-- List -->
    <view class="nf-list" v-if="auth.isLoggedIn">
      <view
        v-for="item in list"
        :key="item.id"
        class="nf-item"
        :class="{ 'nf-item-unread': !item.read }"
        @tap="markAsRead(item); goDetail(item.imageId)"
      >
        <view
          class="nf-item-icon-wrap"
          :style="{ background: getTypeBg(item.type), borderColor: getTypeBorder(item.type) }"
        >
          <text class="nf-item-icon">{{ getTypeIcon(item.type) }}</text>
        </view>
        <view class="nf-item-body">
          <view class="nf-item-head">
            <text class="nf-item-title">{{ item.title }}</text>
            <view class="nf-item-dot" v-if="!item.read" />
          </view>
          <text class="nf-item-content">{{ item.content }}</text>
          <text class="nf-item-time">{{ item.time }}</text>
        </view>
        <text class="nf-item-arrow">›</text>
      </view>
    </view>

    <view class="nf-bottom" />
  </view>
</template>

<style>
/* === Notifications Page === */
.nf-page {
  min-height: 100vh;
  padding-bottom: 60px;
}

/* Header */
.nf-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px 16px;
}
.nf-title {
  font-size: 38px;
  font-weight: 800;
  color: #1e293b;
}
.nf-header-right {
  display: flex;
  flex-direction: row;
  align-items: center;
}
.nf-unread {
  font-size: 22px;
  color: #5b5fe3;
  background: #f0f0ff;
  padding: 4px 12px;
  border-radius: 10px;
  margin-right: 12px;
}
.nf-mark-all {
  font-size: 24px;
  color: #5b5fe3;
}
.nf-all-read {
  font-size: 24px;
  color: #94a3b8;
}

/* Empty */
.nf-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 160px;
}
.nf-empty-icon {
  font-size: 80px;
  margin-bottom: 20px;
}
.nf-empty-text {
  font-size: 28px;
  color: #94a3b8;
}

/* List */
.nf-list {
  padding: 8px 28px 0;
  display: flex;
  flex-direction: column;
}
.nf-item {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  padding: 24px 20px;
  background: #fff;
  border-radius: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  position: relative;
}
.nf-item-unread {
  background: #fafaff;
}
.nf-item-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 16px;
  border: 2px solid #e2e8f0;
}
.nf-item-icon {
  font-size: 30px;
}
.nf-item-body {
  flex: 1;
  min-width: 0;
}
.nf-item-head {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 6px;
}
.nf-item-title {
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
}
.nf-item-dot {
  width: 8px;
  height: 8px;
  border-radius: 4px;
  background: #ef4444;
  margin-left: 8px;
  flex-shrink: 0;
}
.nf-item-content {
  display: block;
  font-size: 25px;
  color: #64748b;
  line-height: 1.5;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.nf-item-time {
  display: block;
  font-size: 22px;
  color: #cbd5e1;
}
.nf-item-arrow {
  font-size: 28px;
  color: #cbd5e1;
  align-self: center;
  margin-left: 8px;
}

.nf-bottom { height: 24px; }
</style>
