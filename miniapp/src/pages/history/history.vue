<script setup lang="ts">
import { ref } from 'vue'
import Taro, { useDidShow, useReachBottom } from '@tarojs/taro'
import { useAuthStore } from '../../stores/auth'
import { getPatientRecords, type DiagnosisRecord } from '../../api/diagnosis'
import StatusBadge from '../../components/StatusBadge.vue'
import CustomTabBar from '../../components/CustomTabBar.vue'

const auth = useAuthStore()
const records = ref<DiagnosisRecord[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const total = ref(0)
const hasMore = ref(true)
const filterStatus = ref('')

const statusFilters = [
  { value: '', label: '全部' },
  { value: 'ai_generated', label: '待审核' },
  { value: 'doctor_reviewed', label: '已审核' },
  { value: 'finalized', label: '已归档' },
]

useDidShow(async () => {
  await auth.init()
  if (auth.isLoggedIn) {
    await loadRecords()
  }
})

async function loadRecords(reset = false) {
  if (loading.value) return
  if (reset) { page.value = 1; records.value = []; hasMore.value = true }
  loading.value = true
  try {
    const res = await getPatientRecords('P-0001', 10, (page.value - 1) * 10)
    if (reset) { records.value = res.items }
    else { records.value = [...records.value, ...res.items] }
    total.value = res.meta.total
    hasMore.value = records.value.length < total.value
  } catch {
    Taro.showToast({ title: '加载失败', icon: 'error' })
  } finally {
    loading.value = false; loadingMore.value = false
  }
}

useReachBottom(() => {
  if (!hasMore.value || loadingMore.value) return
  loadingMore.value = true; page.value++; loadRecords(false)
})

function switchFilter(status: string) {
  filterStatus.value = status
}

function goDetail(imageId: string) {
  Taro.navigateTo({ url: `/pages/result/result?imageId=${imageId}` })
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = dateStr.slice(0, 10)
  const t = dateStr.slice(11, 16) || ''
  return `${d.replace(/-/g, '/')} ${t}`
}

function goLogin() {
  Taro.navigateTo({ url: '/pages/login/login' })
}

function goUpload() {
  Taro.chooseImage({
    count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'],
    success: (res) => {
      Taro.navigateTo({ url: `/pages/result/result?filePath=${encodeURIComponent(res.tempFilePaths[0])}` })
    },
  })
}
</script>

<template>
  <view class="his-page">
    <!-- Not logged in -->
    <view v-if="!auth.isLoggedIn && auth.ready" class="his-empty-wrap">
      <text class="his-empty-icon">🔒</text>
      <text class="his-empty-text">登录后查看检测记录</text>
      <text class="his-empty-sub">登录即可查看所有历史影像分析记录</text>
      <view class="his-empty-action">
        <button class="his-btn-primary" @tap="goLogin">立即登录</button>
      </view>
    </view>

    <!-- Loading skeleton -->
    <view v-if="!auth.ready" class="his-skeleton">
      <view v-for="i in 4" :key="i" class="his-skel-item">
        <view class="his-skel-line his-skel-w40" />
        <view class="his-skel-line his-skel-w60" />
      </view>
    </view>

    <!-- Tabs -->
    <view class="his-tabs" v-if="auth.isLoggedIn && records.length > 0">
      <scroll-view scroll-x class="his-tabs-scroll" :show-scrollbar="false">
        <view class="his-tabs-wrap">
          <view
            v-for="f in statusFilters" :key="f.value"
            class="his-tab"
            :class="{ 'his-tab-active': filterStatus === f.value }"
            @tap="switchFilter(f.value)"
          >
            <text>{{ f.label }}</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- Empty -->
    <view v-if="auth.isLoggedIn && !loading && records.length === 0" class="his-empty-wrap">
      <text class="his-empty-icon">📭</text>
      <text class="his-empty-text">暂无检测记录</text>
      <text class="his-empty-sub">上传牙片后检测记录将显示在这里</text>
      <view class="his-empty-action">
        <button class="his-btn-primary" @tap="goUpload">上传影像</button>
      </view>
    </view>

    <!-- List -->
    <view class="his-list" v-if="auth.isLoggedIn && records.length > 0">
      <view
        v-for="r in records" :key="r.image_id"
        class="his-item"
        @tap="goDetail(r.image_id)"
      >
        <view class="his-item-left">
          <view class="his-item-thumb"><text>🦷</text></view>
          <view class="his-item-info">
            <text class="his-item-name">{{ r.filename || '牙科影像' }}</text>
            <text class="his-item-meta">{{ r.image_type === 'panoramic' ? '全景片' : r.image_type === 'periapical' ? '根尖片' : r.image_type }} · {{ formatDate(r.created_at) }}</text>
          </view>
        </view>
        <view class="his-item-right">
          <StatusBadge :status="r.report.status" />
          <text class="his-item-arrow">›</text>
        </view>
      </view>

      <view class="his-footer" v-if="loadingMore">
        <text class="his-footer-text">加载中...</text>
      </view>
      <view class="his-footer" v-else-if="!hasMore">
        <text class="his-footer-text">共 {{ total }} 条记录</text>
      </view>
    </view>

    <CustomTabBar :current="1" />
  </view>
</template>

<style>
/* === History Page === */
.his-page { min-height: 100vh; padding: 20px 28px 48px; }

/* Empty */
.his-empty-wrap { display: flex; flex-direction: column; align-items: center; padding: 160px 48px 0; }
.his-empty-icon { font-size: 100px; margin-bottom: 24px; }
.his-empty-text { font-size: 30px; font-weight: 600; color: #1e293b; display: block; text-align: center; }
.his-empty-sub { font-size: 26px; color: #94a3b8; margin-top: 8px; display: block; text-align: center; }
.his-empty-action { margin-top: 32px; }
.his-btn-primary { background: #5b5fe3; color: #fff; border: none; border-radius: 16px; font-size: 30px; font-weight: 600; padding: 0 48px; height: 88px; line-height: 88px; }

/* Skeleton */
.his-skeleton { display: flex; flex-direction: column; }
.his-skel-item { padding: 28px 24px; background: #fff; border-radius: 16px; margin-bottom: 16px; }
.his-skel-line { height: 18px; border-radius: 4px; background: #e2e8f0; margin-bottom: 10px; }
.his-skel-w40 { width: 40%; height: 22px; }
.his-skel-w60 { width: 60%; }

/* Tabs */
.his-tabs { margin-bottom: 16px; }
.his-tabs-wrap { display: flex; flex-direction: row; }
.his-tab { padding: 14px 24px; border-radius: 12px; font-size: 26px; color: #64748b; background: #f1f5f9; flex-shrink: 0; margin-right: 12px; }
.his-tab:last-child { margin-right: 0; }
.his-tab-active { background: #5b5fe3; color: #fff; }

/* List */
.his-list { display: flex; flex-direction: column; }
.his-item { display: flex; flex-direction: row; align-items: center; justify-content: space-between; padding: 24px 20px; background: #fff; margin-bottom: 12px; border-radius: 16px; }
.his-item-left { display: flex; flex-direction: row; align-items: center; flex: 1; min-width: 0; }
.his-item-thumb { width: 64px; height: 64px; border-radius: 14px; background: #f0f0ff; display: flex; align-items: center; justify-content: center; font-size: 32px; flex-shrink: 0; margin-right: 16px; }
.his-item-info { flex: 1; min-width: 0; }
.his-item-name { display: block; font-size: 28px; font-weight: 500; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.his-item-meta { display: block; font-size: 22px; color: #94a3b8; margin-top: 6px; }
.his-item-right { display: flex; flex-direction: row; align-items: center; flex-shrink: 0; }
.his-item-arrow { font-size: 32px; color: #cbd5e1; margin-left: 12px; }

.his-footer { padding: 20px 0; text-align: center; }
.his-footer-text { font-size: 24px; color: #cbd5e1; }
</style>
