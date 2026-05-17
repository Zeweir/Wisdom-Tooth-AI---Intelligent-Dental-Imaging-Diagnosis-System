<script setup lang="ts">
import { ref, computed } from 'vue'
import Taro, { useLoad } from '@tarojs/taro'

interface Detection {
  bbox: number[]
  class: string
  confidence: number
  severity: string
  tooth_id: string
  finding_label?: string
}

const imageUrl = ref('')
const detections = ref<Detection[]>([])
const imageId = ref('')
const showDetections = ref(true)
const loading = ref(true)
const error = ref('')

// Color map for detection classes
const classColors: Record<string, string> = {
  '智齿阻生': '#ef4444',
  '龋齿': '#f59e0b',
  '根尖周炎': '#8b5cf6',
  '牙槽骨吸收': '#06b6d4',
  '冠周炎': '#f97316',
  '缺失牙': '#6b7280',
  '充填体': '#84cc16',
}

useLoad(async (opts) => {
  imageId.value = opts?.imageId || ''
  const fp = decodeURIComponent(opts?.filePath || '')

  if (imageId.value) {
    try {
      // Fetch image file URL and analysis data
      const token = Taro.getStorageSync('access_token') || ''
      const baseUrl = 'https://your-server.com'

      // In production, fetch the actual image and analysis
      imageUrl.value = fp || ''
      try {
        const analysisRes = await Taro.request({
          url: `${baseUrl}/api/v1/analysis/${imageId.value}`,
          header: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (analysisRes.statusCode === 200 && analysisRes.data?.code === 200) {
          const data = analysisRes.data.data
          detections.value = (data.detections || []).map((d: any) => ({
            bbox: d.bbox || [0, 0, 0, 0],
            class: d.class || '待确认',
            confidence: d.confidence || 0,
            severity: d.severity || '待确认',
            tooth_id: d.tooth_id || '',
            finding_label: d.finding_label || d.class || '',
          }))
        }
      } catch { /* detection fetch optional */ }
    } catch {
      error.value = '加载失败'
    }
  } else if (fp) {
    imageUrl.value = fp
  }
  loading.value = false
})

function getColor(className: string) {
  for (const [key, color] of Object.entries(classColors)) {
    if (className.includes(key)) return color
  }
  return '#5b5fe3'
}

function getBoxStyle(d: Detection) {
  const [x1, y1, x2, y2] = d.bbox
  return {
    left: x1 + 'px',
    top: y1 + 'px',
    width: (x2 - x1) + 'px',
    height: (y2 - y1) + 'px',
    borderColor: getColor(d.class),
  }
}

function getBoxLabel(d: Detection) {
  const label = d.finding_label || d.class
  return `${label} ${Math.round(d.confidence * 100)}%`
}

function toggleDetections() {
  showDetections.value = !showDetections.value
}

function goBack() {
  Taro.navigateBack()
}
</script>

<template>
  <view class="iv-page">
    <!-- Full screen image area -->
    <view class="iv-canvas">
      <view class="iv-image-wrap">
        <image
          class="iv-image"
          :src="imageUrl || '/static/logo.png'"
          mode="aspectFit"
        />
        <!-- Detection boxes overlay -->
        <view class="iv-overlay" v-if="showDetections && detections.length > 0">
          <view
            v-for="(d, idx) in detections"
            :key="idx"
            class="iv-box"
            :style="getBoxStyle(d)"
          >
            <view
              class="iv-box-label"
              :style="{ background: getColor(d.class) }"
            >
              <text>{{ getBoxLabel(d) }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- Bottom controls -->
    <view class="iv-controls">
      <view class="iv-ctrl-left">
        <view class="iv-ctrl-btn" v-if="detections.length > 0" @tap="toggleDetections">
          <text class="iv-ctrl-icon">{{ showDetections ? '👁' : '👁‍🗨' }}</text>
          <text class="iv-ctrl-label">{{ showDetections ? '隐藏标注' : '显示标注' }}</text>
        </view>
      </view>
      <view class="iv-ctrl-right">
        <view class="iv-ctrl-btn" @tap="goBack">
          <text class="iv-ctrl-icon">✕</text>
          <text class="iv-ctrl-label">关闭</text>
        </view>
      </view>
    </view>

    <!-- Detection list drawer -->
    <view class="iv-drawer" v-if="showDetections && detections.length > 0">
      <text class="iv-drawer-title">检测发现 ({{ detections.length }})</text>
      <scroll-view scroll-y class="iv-drawer-list">
        <view v-for="(d, idx) in detections" :key="idx" class="iv-det-item">
          <view class="iv-det-dot" :style="{ background: getColor(d.class) }" />
          <view class="iv-det-info">
            <text class="iv-det-class">{{ d.finding_label || d.class }}</text>
            <text class="iv-det-meta">牙位 {{ d.tooth_id || '未知' }} · {{ d.severity }} · {{ Math.round(d.confidence * 100) }}%</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- Loading / Error -->
    <view v-if="loading" class="iv-loading">
      <text>加载中...</text>
    </view>
    <view v-if="error" class="iv-error">
      <text>{{ error }}</text>
      <view class="iv-error-back" @tap="goBack"><text>返回</text></view>
    </view>
  </view>
</template>

<style>
/* === Image Viewer === */
.iv-page {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: #000;
  z-index: 500;
  display: flex;
  flex-direction: column;
}

.iv-canvas {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.iv-image-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.iv-image {
  width: 100%;
  height: 100%;
}
.iv-overlay {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
}

/* Detection boxes */
.iv-box {
  position: absolute;
  border: 2px solid;
  border-radius: 4px;
}
.iv-box-label {
  position: absolute;
  top: -28px;
  left: -1px;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}
.iv-box-label text {
  font-size: 18px;
  color: #fff;
}

/* Controls */
.iv-controls {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  padding-bottom: calc(16px + constant(safe-area-inset-bottom));
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
  background: rgba(0,0,0,0.7);
}
.iv-ctrl-left, .iv-ctrl-right {
  display: flex; flex-direction: row; align-items: center;
}
.iv-ctrl-btn {
  display: flex; flex-direction: column; align-items: center;
  padding: 8px 16px;
}
.iv-ctrl-icon { font-size: 28px; line-height: 1.2; }
.iv-ctrl-label { font-size: 20px; color: rgba(255,255,255,0.7); margin-top: 2px; }

/* Drawer */
.iv-drawer {
  background: rgba(20,20,30,0.95);
  padding: 20px 24px;
  max-height: 240px;
}
.iv-drawer-title {
  font-size: 26px; font-weight: 600; color: #fff;
  display: block; margin-bottom: 12px;
}
.iv-drawer-list { max-height: 180px; }
.iv-det-item {
  display: flex; flex-direction: row; align-items: center;
  padding: 10px 0;
}
.iv-det-dot {
  width: 8px; height: 8px; border-radius: 4px;
  margin-right: 10px; flex-shrink: 0;
}
.iv-det-info { flex: 1; display: flex; flex-direction: column; }
.iv-det-class { font-size: 24px; color: #fff; font-weight: 500; }
.iv-det-meta { font-size: 20px; color: rgba(255,255,255,0.5); margin-top: 2px; }

.iv-loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); }
.iv-loading text { color: #fff; font-size: 28px; }
.iv-error { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); display: flex; flex-direction: column; align-items: center; }
.iv-error text { color: #fff; font-size: 28px; }
.iv-error-back { margin-top: 16px; padding: 12px 32px; background: rgba(255,255,255,0.15); border-radius: 20px; }
.iv-error-back text { font-size: 26px; color: #fff; }
</style>
