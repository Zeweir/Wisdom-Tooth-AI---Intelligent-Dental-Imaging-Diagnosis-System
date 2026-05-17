<script setup lang="ts">
import { ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { useAuthStore } from '../../stores/auth'
import { getPatientRecords, type DiagnosisRecord } from '../../api/diagnosis'
import CustomTabBar from '../../components/CustomTabBar.vue'

const auth = useAuthStore()
const recentRecords = ref<DiagnosisRecord[]>([])
const dashboardStats = ref({ total: 0, finalized: 0, pending: 0 })
const loadingStats = ref(false)

async function loadData() {
  await auth.init()
  if (auth.isLoggedIn) {
    loadingStats.value = true
    try {
      const res = await getPatientRecords('P-0001', 5, 0)
      recentRecords.value = res.items
      dashboardStats.value.total = res.meta.total
      dashboardStats.value.finalized = res.items.filter(i => i.report.status === 'finalized').length
      dashboardStats.value.pending = res.items.filter(i => i.report.status === 'ai_generated').length
    } catch { /* silent */ }
    finally { loadingStats.value = false }
  }
}

useDidShow(() => {
  loadData()
})

function goLogin() {
  Taro.navigateTo({ url: '/pages/login/login' })
}

function handleQuiz() {
  if (!auth.isLoggedIn) { goLogin(); return }
  Taro.navigateTo({ url: '/pages/quiz/quiz' })
}

function handleUpload() {
  if (!auth.isLoggedIn) { goLogin(); return }
  Taro.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      Taro.navigateTo({ url: `/pages/result/result?filePath=${encodeURIComponent(res.tempFilePaths[0])}` })
    },
  })
}

function goHistory() {
  if (!auth.isLoggedIn) { goLogin(); return }
  Taro.switchTab({ url: '/pages/history/history' })
}

function goDetail(imageId: string) {
  Taro.navigateTo({ url: `/pages/result/result?imageId=${imageId}` })
}

function getStatusTag(status: string) {
  const map: Record<string, string> = {
    processing: '分析中', ai_generated: '待审核',
    doctor_reviewed: '已审核', finalized: '已归档',
  }
  return map[status] ?? status
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return dateStr.slice(0, 10).replace(/-/g, '/')
}
</script>

<template>
  <view class="idx-page">
    <!-- Header -->
    <view class="idx-header">
      <view class="idx-header-bar">
        <view class="idx-header-left">
          <image class="idx-header-logo" src="/static/logo.png" mode="aspectFit" />
          <view class="idx-header-texts">
            <text class="idx-header-title">智齿 AI</text>
            <text class="idx-header-sub">牙齿影像智能诊断</text>
          </view>
        </view>
        <view class="idx-header-right" @tap="Taro.switchTab({ url: '/pages/me/me' })">
          <text class="idx-avatar">{{ auth.isLoggedIn ? auth.displayName.slice(0, 1) : '?' }}</text>
        </view>
      </view>
    </view>

    <!-- Welcome -->
    <view class="idx-welcome" v-if="auth.isLoggedIn">
      <text class="idx-welcome-text">你好，{{ auth.displayName }}</text>
      <text class="idx-welcome-role">{{ auth.user?.role_label }}</text>
    </view>

    <!-- Dashboard -->
    <view class="idx-stats" v-if="auth.isLoggedIn && !loadingStats">
      <view class="idx-stat idx-stat-primary">
        <text class="idx-stat-num">{{ dashboardStats.total || recentRecords.length }}</text>
        <text class="idx-stat-label">总检测</text>
      </view>
      <view class="idx-stat idx-stat-success">
        <text class="idx-stat-num">{{ dashboardStats.finalized }}</text>
        <text class="idx-stat-label">已归档</text>
      </view>
      <view class="idx-stat idx-stat-warn">
        <text class="idx-stat-num">{{ dashboardStats.pending }}</text>
        <text class="idx-stat-label">待审核</text>
      </view>
    </view>

    <!-- Quick Actions -->
    <view class="idx-section">
      <text class="idx-section-title">快捷操作</text>
      <view class="idx-actions">
        <view class="idx-action" @tap="handleUpload">
          <view class="idx-action-icon idx-action-icon-upload">
            <text class="idx-action-emoji">🦷</text>
          </view>
          <text class="idx-action-label">AI 影像分析</text>
          <text class="idx-action-desc">上传牙片，智能诊断</text>
          <view class="idx-action-tag">
            <text>立即使用</text>
            <text class="idx-action-arrow">→</text>
          </view>
        </view>
        <view class="idx-action idx-action-gap" @tap="handleQuiz">
          <view class="idx-action-icon idx-action-icon-quiz">
            <text class="idx-action-emoji">📋</text>
          </view>
          <text class="idx-action-label">症状自测</text>
          <text class="idx-action-desc">回答问题，评估风险</text>
          <view class="idx-action-tag">
            <text>开始测评</text>
            <text class="idx-action-arrow">→</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Recent Records -->
    <view class="idx-section" v-if="auth.isLoggedIn && recentRecords.length > 0">
      <view class="idx-section-head">
        <text class="idx-section-title">最近记录</text>
        <text class="idx-section-link" @tap="goHistory">查看全部 ›</text>
      </view>
      <view class="idx-records">
        <view
          v-for="r in recentRecords.slice(0, 3)"
          :key="r.image_id"
          class="idx-record"
          @tap="goDetail(r.image_id)"
        >
          <view class="idx-record-left">
            <text class="idx-record-name">{{ r.filename || '牙科影像' }}</text>
            <text class="idx-record-date">{{ formatDate(r.created_at) }}</text>
          </view>
          <view class="idx-record-right">
            <text class="idx-record-tag" :class="'idx-tag-' + (r.report.status || 'processing')">
              {{ getStatusTag(r.report.status) }}
            </text>
            <text class="idx-record-arr">›</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Hero (not logged in) -->
    <view class="idx-hero" v-if="!auth.isLoggedIn">
      <view class="idx-hero-circle">
        <image class="idx-hero-logo" src="/static/logo.png" mode="aspectFit" />
      </view>
      <text class="idx-hero-title">智齿 AI</text>
      <text class="idx-hero-sub">牙齿影像智能诊断助手</text>
      <view class="idx-hero-btns">
        <view class="idx-hero-btn idx-hero-btn-primary" @tap="goLogin">
          <text>登录使用</text>
        </view>
        <view class="idx-hero-btn idx-hero-btn-outline idx-hero-btn-ml" @tap="handleQuiz">
          <text>先体验自测</text>
        </view>
      </view>
      <view class="idx-hero-steps">
        <view class="idx-hero-step">
          <text class="idx-hero-step-num">1</text>
          <text class="idx-hero-step-txt">拍照或上传牙片</text>
        </view>
        <view class="idx-hero-step-line" />
        <view class="idx-hero-step">
          <text class="idx-hero-step-num">2</text>
          <text class="idx-hero-step-txt">AI 秒级分析</text>
        </view>
        <view class="idx-hero-step-line" />
        <view class="idx-hero-step">
          <text class="idx-hero-step-num">3</text>
          <text class="idx-hero-step-txt">获取诊断报告</text>
        </view>
      </view>
    </view>

    <CustomTabBar :current="0" />
  </view>
</template>

<style>
/* === Index Page === */
.idx-page {
  min-height: 100vh;
  padding-bottom: 48px;
}

/* Header */
.idx-header {
  padding: 12px 28px;
  background: #fff;
}
.idx-header-bar {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}
.idx-header-left {
  display: flex;
  flex-direction: row;
  align-items: center;
}
.idx-header-logo {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  margin-right: 12px;
}
.idx-header-texts {
  display: flex;
  flex-direction: column;
}
.idx-header-title {
  font-size: 30px;
  font-weight: 700;
  color: #1e293b;
  display: block;
  line-height: 1.3;
}
.idx-header-sub {
  font-size: 22px;
  color: #94a3b8;
  display: block;
  line-height: 1.3;
}
.idx-header-right {
  width: 64px;
  height: 64px;
}
.idx-avatar {
  display: block;
  width: 64px;
  height: 64px;
  line-height: 64px;
  text-align: center;
  background: #5b5fe3;
  color: #fff;
  border-radius: 32px;
  font-size: 28px;
  font-weight: 600;
}

/* Welcome */
.idx-welcome {
  padding: 24px 28px 12px;
}
.idx-welcome-text {
  display: block;
  font-size: 38px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.3;
}
.idx-welcome-role {
  display: inline-block;
  font-size: 22px;
  color: #5b5fe3;
  background: #f0f0ff;
  padding: 4px 14px;
  border-radius: 20px;
  margin-top: 8px;
}

/* Stats */
.idx-stats {
  display: flex;
  flex-direction: row;
  padding: 24px 28px;
}
.idx-stat {
  flex: 1;
  padding: 24px 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 16px;
}
.idx-stat:last-child { margin-right: 0; }
.idx-stat-primary { background: #f0f0ff; }
.idx-stat-success { background: #ecfdf5; }
.idx-stat-warn { background: #fffbeb; }
.idx-stat-num {
  font-size: 48px;
  font-weight: 800;
  line-height: 1.1;
}
.idx-stat-primary .idx-stat-num { color: #5b5fe3; }
.idx-stat-success .idx-stat-num { color: #10b981; }
.idx-stat-warn .idx-stat-num { color: #f59e0b; }
.idx-stat-label {
  font-size: 22px;
  color: #64748b;
  margin-top: 6px;
}

/* Section */
.idx-section {
  padding: 12px 28px;
}
.idx-section-head {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}
.idx-section-title {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  display: block;
}
.idx-section-link {
  font-size: 26px;
  color: #5b5fe3;
}

/* Actions */
.idx-actions {
  display: flex;
  flex-direction: row;
  margin-top: 20px;
}
.idx-action {
  flex: 1;
  padding: 28px 20px;
  background: #fff;
  border-radius: 20px;
  position: relative;
  overflow: hidden;
}
.idx-action-gap { margin-left: 16px; }
.idx-action-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}
.idx-action-icon-upload { background: #ecfdf5; }
.idx-action-icon-quiz { background: #f0f0ff; }
.idx-action-emoji { font-size: 32px; line-height: 1; }
.idx-action-label {
  display: block;
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}
.idx-action-desc {
  display: block;
  font-size: 22px;
  color: #94a3b8;
  margin-bottom: 14px;
}
.idx-action-tag {
  display: flex;
  flex-direction: row;
  align-items: center;
  font-size: 22px;
  color: #5b5fe3;
  font-weight: 500;
}
.idx-action-arrow { font-size: 24px; margin-left: 4px; }

/* Records */
.idx-records {
  margin-top: 16px;
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
}
.idx-record {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid #f1f5f9;
}
.idx-record:last-child { border-bottom: 0; }
.idx-record-left { flex: 1; min-width: 0; }
.idx-record-name {
  display: block;
  font-size: 28px;
  font-weight: 500;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.idx-record-date {
  display: block;
  font-size: 22px;
  color: #94a3b8;
  margin-top: 4px;
}
.idx-record-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-shrink: 0;
}
.idx-record-tag {
  font-size: 20px;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
}
.idx-tag-processing { background: #fef3c7; color: #d97706; }
.idx-tag-ai_generated { background: #dbeafe; color: #2563eb; }
.idx-tag-doctor_reviewed { background: #d1fae5; color: #059669; }
.idx-tag-finalized { background: #f3f4f6; color: #6b7280; }
.idx-record-arr {
  font-size: 32px;
  color: #cbd5e1;
  margin-left: 12px;
}

/* Hero */
.idx-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 48px 0;
}
.idx-hero-circle {
  width: 140px;
  height: 140px;
  border-radius: 70px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28px;
  box-shadow: 0 8px 40px rgba(91,95,227,0.12);
}
.idx-hero-logo { width: 100px; height: 100px; border-radius: 20px; }
.idx-hero-title { font-size: 52px; font-weight: 800; color: #1e293b; }
.idx-hero-sub { font-size: 28px; color: #64748b; margin-top: 10px; }
.idx-hero-btns {
  display: flex;
  flex-direction: row;
  margin-top: 36px;
}
.idx-hero-btn {
  height: 88px;
  border-radius: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  font-weight: 600;
  padding: 0 36px;
}
.idx-hero-btn-primary { background: #5b5fe3; color: #fff; }
.idx-hero-btn-outline {
  background: #fff;
  color: #5b5fe3;
  border: 2px solid #5b5fe3;
}
.idx-hero-btn-ml { margin-left: 16px; }

.idx-hero-steps {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-top: 56px;
  width: 100%;
  padding: 0 24px;
}
.idx-hero-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}
.idx-hero-step-num {
  width: 52px;
  height: 52px;
  line-height: 52px;
  text-align: center;
  background: #5b5fe3;
  color: #fff;
  border-radius: 26px;
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 10px;
}
.idx-hero-step-txt { font-size: 22px; color: #64748b; text-align: center; }
.idx-hero-step-line {
  width: 40px;
  height: 2px;
  background: #e2e8f0;
  margin-bottom: 24px;
}
</style>
