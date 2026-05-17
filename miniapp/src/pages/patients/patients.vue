<script setup lang="ts">
import { ref } from 'vue'
import Taro, { useDidShow, useReachBottom } from '@tarojs/taro'
import { useAuthStore } from '../../stores/auth'
import { listPatients, type PatientRecord } from '../../api/patients'

const auth = useAuthStore()
const patients = ref<PatientRecord[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const keyword = ref('')
const page = ref(1)
const total = ref(0)
const hasMore = ref(true)

useDidShow(async () => {
  await auth.init()
  if (auth.isLoggedIn) { await loadPatients(true) }
})

async function loadPatients(reset = false) {
  if (loading.value) return
  if (reset) { page.value = 1; patients.value = []; hasMore.value = true }
  loading.value = true
  try {
    const res = await listPatients(keyword.value, 15, (page.value - 1) * 15)
    if (reset) { patients.value = res.data }
    else { patients.value = [...patients.value, ...res.data] }
    total.value = res.meta.total
    hasMore.value = patients.value.length < total.value
  } catch { /* offline */ }
  finally { loading.value = false; loadingMore.value = false }
}

useReachBottom(() => {
  if (!hasMore.value || loadingMore.value) return
  loadingMore.value = true; page.value++; loadPatients(false)
})

function onSearch() {
  loadPatients(true)
}

function clearSearch() {
  keyword.value = ''
  loadPatients(true)
}

function goDetail(patientId: string) {
  Taro.navigateTo({ url: `/pages/patient-detail/patient-detail?patientId=${patientId}` })
}

function getGenderTag(gender: string | null) {
  if (!gender) return ''
  return gender === '男' ? '♂' : gender === '女' ? '♀' : ''
}

function getGenderColor(gender: string | null) {
  if (!gender) return '#94a3b8'
  return gender === '男' ? '#3b82f6' : '#ec4899'
}

function getAvatarBg(name: string) {
  const colors = ['#5b5fe3', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
  const idx = (name || 'A').charCodeAt(0) % colors.length
  return colors[idx]
}

function formatDate(s: string | null) {
  if (!s) return '暂无记录'
  return s.slice(0, 10).replace(/-/g, '/')
}

function goUpload(patientId: string) {
  Taro.chooseImage({
    count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'],
    success: (res) => {
      Taro.navigateTo({
        url: `/pages/result/result?filePath=${encodeURIComponent(res.tempFilePaths[0])}&patientId=${patientId}`
      })
    },
  })
}
</script>

<template>
  <view class="pt-page">
    <!-- Search -->
    <view class="pt-search">
      <view class="pt-search-bar">
        <text class="pt-search-icon">🔍</text>
        <input
          v-model="keyword"
          class="pt-search-inp"
          placeholder="搜索患者姓名或ID"
          placeholder-class="pt-search-ph"
          @confirm="onSearch"
        />
        <text class="pt-search-clear" v-if="keyword" @tap="clearSearch">✕</text>
      </view>
    </view>

    <!-- Not logged in -->
    <view v-if="!auth.isLoggedIn && auth.ready" class="pt-empty">
      <text class="pt-empty-icon">🔒</text>
      <text class="pt-empty-text">登录后查看患者档案</text>
    </view>

    <!-- Loading -->
    <view v-if="auth.isLoggedIn && loading && patients.length === 0" class="pt-skel">
      <view v-for="i in 5" :key="i" class="pt-skel-item">
        <view class="pt-skel-avatar" />
        <view class="pt-skel-info">
          <view class="pt-skel-line pt-skel-w50" />
          <view class="pt-skel-line pt-skel-w80" />
        </view>
      </view>
    </view>

    <!-- Empty -->
    <view v-if="auth.isLoggedIn && !loading && patients.length === 0" class="pt-empty">
      <text class="pt-empty-icon">👥</text>
      <text class="pt-empty-text">{{ keyword ? '未找到匹配患者' : '暂无患者数据' }}</text>
      <text class="pt-empty-sub" v-if="!keyword">上传影像时将自动创建患者档案</text>
    </view>

    <!-- List -->
    <view class="pt-list" v-if="patients.length > 0">
      <view
        v-for="p in patients"
        :key="p.patient_id"
        class="pt-card"
        @tap="goDetail(p.patient_id)"
      >
        <view class="pt-card-avatar" :style="{ background: getAvatarBg(p.name) }">
          <text>{{ (p.name || '?')[0] }}</text>
        </view>
        <view class="pt-card-body">
          <view class="pt-card-row">
            <text class="pt-card-name">{{ p.name || p.patient_id }}</text>
            <text
              class="pt-card-gender"
              v-if="p.gender"
              :style="{ color: getGenderColor(p.gender) }"
            >{{ getGenderTag(p.gender) }} {{ p.gender }}</text>
          </view>
          <view class="pt-card-row pt-card-meta">
            <text class="pt-card-id">{{ p.patient_id }}</text>
            <text class="pt-card-age" v-if="p.age">{{ p.age }}岁</text>
          </view>
          <view class="pt-card-stats">
            <view class="pt-card-stat">
              <text class="pt-stat-num">{{ p.image_count }}</text>
              <text class="pt-stat-label">影像</text>
            </view>
            <view class="pt-card-stat">
              <text class="pt-stat-date">{{ formatDate(p.latest_image_at) }}</text>
              <text class="pt-stat-label">最近检查</text>
            </view>
            <view class="pt-card-action" @tap.stop="goUpload(p.patient_id)">
              <text>+ 上传</text>
            </view>
          </view>
        </view>
        <text class="pt-card-arrow">›</text>
      </view>

      <view class="pt-footer" v-if="loadingMore">
        <text class="pt-footer-text">加载中...</text>
      </view>
      <view class="pt-footer" v-else-if="!hasMore && patients.length > 0">
        <text class="pt-footer-text">共 {{ total }} 位患者</text>
      </view>
    </view>
  </view>
</template>

<style>
/* === Patients Page === */
.pt-page { min-height: 100vh; padding-bottom: 48px; }

/* Search */
.pt-search { padding: 20px 28px; }
.pt-search-bar {
  display: flex; flex-direction: row; align-items: center;
  background: #fff; border-radius: 16px; padding: 0 20px;
  height: 80px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.pt-search-icon { font-size: 28px; margin-right: 12px; }
.pt-search-inp { flex: 1; font-size: 28px; color: #1e293b; height: 100%; border: none; outline: none; background: transparent; }
.pt-search-ph { color: #cbd5e1; font-size: 28px; }
.pt-search-clear { font-size: 26px; color: #94a3b8; padding: 8px; }

/* Empty */
.pt-empty { display: flex; flex-direction: column; align-items: center; padding-top: 140px; }
.pt-empty-icon { font-size: 80px; margin-bottom: 20px; }
.pt-empty-text { font-size: 30px; font-weight: 600; color: #1e293b; }
.pt-empty-sub { font-size: 24px; color: #94a3b8; margin-top: 8px; }

/* Skeleton */
.pt-skel { padding: 0 28px; }
.pt-skel-item {
  display: flex; flex-direction: row; align-items: center;
  background: #fff; border-radius: 16px; padding: 24px 20px; margin-bottom: 12px;
}
.pt-skel-avatar {
  width: 64px; height: 64px; border-radius: 16px;
  background: #e2e8f0; margin-right: 16px; flex-shrink: 0;
}
.pt-skel-info { flex: 1; }
.pt-skel-line { height: 18px; background: #e2e8f0; border-radius: 4px; margin-bottom: 10px; }
.pt-skel-w50 { width: 50%; height: 24px; }
.pt-skel-w80 { width: 80%; }

/* Cards */
.pt-list { padding: 0 28px; display: flex; flex-direction: column; }
.pt-card {
  display: flex; flex-direction: row; align-items: center;
  background: #fff; border-radius: 20px; padding: 24px 20px;
  margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.pt-card-avatar {
  width: 64px; height: 64px; border-radius: 18px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-right: 16px;
}
.pt-card-avatar text { font-size: 30px; font-weight: 700; color: #fff; }
.pt-card-body { flex: 1; min-width: 0; }
.pt-card-row { display: flex; flex-direction: row; align-items: center; }
.pt-card-name { font-size: 30px; font-weight: 600; color: #1e293b; }
.pt-card-gender { font-size: 24px; margin-left: 8px; }
.pt-card-meta { margin-top: 4px; }
.pt-card-id { font-size: 22px; color: #94a3b8; }
.pt-card-age { font-size: 22px; color: #94a3b8; margin-left: 12px; }

.pt-card-stats {
  display: flex; flex-direction: row; align-items: center;
  margin-top: 14px; padding-top: 14px; border-top: 1px solid #f8fafc;
}
.pt-card-stat {
  display: flex; flex-direction: column;
  margin-right: 28px;
}
.pt-stat-num { font-size: 24px; font-weight: 600; color: #1e293b; line-height: 1.2; }
.pt-stat-date { font-size: 24px; font-weight: 500; color: #1e293b; line-height: 1.2; }
.pt-stat-label { font-size: 20px; color: #94a3b8; margin-top: 2px; }
.pt-card-action {
  margin-left: auto; padding: 10px 20px; background: #5b5fe3;
  border-radius: 20px; font-size: 22px; color: #fff; font-weight: 500;
}
.pt-card-arrow { font-size: 28px; color: #cbd5e1; margin-left: 8px; }

.pt-footer { padding: 20px 0; text-align: center; }
.pt-footer-text { font-size: 24px; color: #cbd5e1; }
</style>
