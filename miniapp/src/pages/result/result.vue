<script setup lang="ts">
import { ref, computed } from 'vue'
import Taro, { useLoad } from '@tarojs/taro'
import { uploadImage, getAnalysis, type DiagnosisRecord } from '../../api/diagnosis'

type PageState = 'pick' | 'preview' | 'uploading' | 'done' | 'error'

const pageState = ref<PageState>('pick')
const progress = ref(0)
const record = ref<DiagnosisRecord | null>(null)
const errorMsg = ref('')
const selectedImage = ref('')

let filePath = ''
let pollTimer: ReturnType<typeof setInterval> | null = null

useLoad((options) => {
  const imageId = options?.imageId || ''
  const fp = decodeURIComponent(options?.filePath || '')
  if (fp) {
    filePath = fp
    selectedImage.value = fp
    pageState.value = 'preview'
  }
  if (imageId) {
    loadExisting(imageId)
  }
})

async function loadExisting(imageId: string) {
  pageState.value = 'uploading'
  progress.value = 60
  try {
    const a = await getAnalysis(imageId)
    if (a.status !== 'processing') {
      record.value = a; pageState.value = 'done'; progress.value = 100
    } else {
      startPolling(imageId)
    }
  } catch {
    errorMsg.value = '加载失败'; pageState.value = 'error'
  }
}

function pickImage() {
  Taro.chooseImage({
    count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'],
    success: (res) => {
      filePath = res.tempFilePaths[0]
      selectedImage.value = res.tempFilePaths[0]
      pageState.value = 'preview'
    },
  })
}

function startUpload() { pageState.value = 'uploading'; progress.value = 0; doUpload() }

async function doUpload() {
  progress.value = 15
  try {
    const result = await uploadImage(filePath, 'P-0001')
    progress.value = 45
    startPolling(result.image_id)
  } catch {
    errorMsg.value = '上传失败，请重试'; pageState.value = 'error'
  }
}

function startPolling(imageId: string) {
  let attempts = 0
  progress.value = 50
  pollTimer = setInterval(async () => {
    attempts++
    progress.value = Math.min(98, 50 + attempts * 3)
    try {
      const a = await getAnalysis(imageId)
      if (a.status !== 'processing') {
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
        record.value = a; progress.value = 100; pageState.value = 'done'
      }
    } catch { /* continue */ }
    if (attempts >= 20) {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
      progress.value = 100
      errorMsg.value = '分析超时，结果稍后可在记录中查看'
      pageState.value = 'error'
    }
  }, 2000)
}

function reupload() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  record.value = null; errorMsg.value = ''; progress.value = 0
  pageState.value = 'pick'; pickImage()
}

function backToHome() { Taro.switchTab({ url: '/pages/index/index' }) }

const statusText = computed(() => {
  if (!record.value) return ''
  const map: Record<string, string> = {
    processing: 'AI 分析中', ai_generated: 'AI 初步分析完成',
    doctor_reviewed: '医生已审核', finalized: '报告已归档',
  }
  return map[record.value.report.status] ?? record.value.report.status
})

const statusIcon = computed(() => {
  if (!record.value) return '📋'
  const map: Record<string, string> = {
    processing: '🔄', ai_generated: '🤖',
    doctor_reviewed: '✅', finalized: '📁',
  }
  return map[record.value.report.status] ?? '📋'
})
</script>

<template>
  <view class="res-page">
    <!-- Pick State -->
    <view v-if="pageState === 'pick'" class="res-pick">
      <text class="res-pick-icon">📸</text>
      <text class="res-pick-title">牙齿影像智能分析</text>
      <text class="res-pick-desc">支持全景片、根尖片、CBCT 影像上传，AI 将自动检测并生成诊断报告</text>
      <view class="res-pick-types">
        <view class="res-pick-type">
          <text class="res-type-icon">🦷</text>
          <text class="res-type-name">全景片</text>
        </view>
        <view class="res-pick-type res-pick-type-ml">
          <text class="res-type-icon">🔍</text>
          <text class="res-type-name">根尖片</text>
        </view>
        <view class="res-pick-type res-pick-type-ml">
          <text class="res-type-icon">💻</text>
          <text class="res-type-name">CBCT</text>
        </view>
      </view>
      <button class="res-pick-btn" @tap="pickImage">选择影像文件</button>
      <text class="res-pick-tip">支持 JPG、PNG 格式，建议清晰度高</text>
    </view>

    <!-- Preview State -->
    <view v-if="pageState === 'preview'" class="res-preview">
      <text class="res-preview-label">影像预览</text>
      <image class="res-preview-img" :src="selectedImage" mode="aspectFit" />
      <view class="res-preview-btns">
        <button class="res-pvbtn res-pvbtn-outline" @tap="pickImage">重新选择</button>
        <button class="res-pvbtn res-pvbtn-primary" @tap="startUpload">开始分析</button>
      </view>
    </view>

    <!-- Uploading State -->
    <view v-if="pageState === 'uploading'" class="res-uploading">
      <view class="res-upload-icons">
        <text class="res-upload-main">🔬</text>
      </view>
      <text class="res-upload-title">AI 正在分析影像</text>
      <text class="res-upload-sub">正在使用深度学习模型检测牙齿病灶...</text>

      <view class="res-progress-wrap">
        <view class="res-progress-bar">
          <view class="res-progress-fill" :style="'width:' + progress + '%'" />
        </view>
        <text class="res-progress-pct">{{ progress }}%</text>
      </view>

      <view class="res-steps">
        <view class="res-step" :class="{ 'res-step-done': progress >= 30 }">
          <text class="res-step-dot" />
          <text class="res-step-label">上传影像</text>
        </view>
        <view class="res-step-line" :class="{ 'res-step-line-on': progress >= 30 }" />
        <view class="res-step" :class="{ 'res-step-done': progress >= 60 }">
          <text class="res-step-dot" />
          <text class="res-step-label">AI 检测</text>
        </view>
        <view class="res-step-line" :class="{ 'res-step-line-on': progress >= 60 }" />
        <view class="res-step" :class="{ 'res-step-done': progress >= 100 }">
          <text class="res-step-dot" />
          <text class="res-step-label">生成报告</text>
        </view>
      </view>
    </view>

    <!-- Done State -->
    <view v-if="pageState === 'done' && record" class="res-done">
      <view class="res-done-status">
        <text class="res-done-icon">{{ statusIcon }}</text>
        <text class="res-done-status-text">{{ statusText }}</text>
      </view>

      <view class="res-report">
        <view class="res-report-head">
          <text class="res-report-title">AI 诊断报告</text>
          <text class="res-report-date">{{ record.created_at?.slice(0, 10) || '' }}</text>
        </view>
        <view class="res-report-divider" />
        <text class="res-report-content">{{ record.report.content }}</text>
      </view>

      <view class="res-report res-report-review" v-if="record.report.doctor_review">
        <view class="res-report-head">
          <text class="res-report-title">👨‍⚕️ 医生审核意见</text>
        </view>
        <view class="res-report-divider" />
        <text class="res-report-content">{{ record.report.doctor_review }}</text>
      </view>

      <view class="res-report" v-if="record.detections && record.detections.length > 0">
        <view class="res-report-head">
          <text class="res-report-title">检测发现 ({{ record.detections.length }})</text>
        </view>
        <view class="res-report-divider" />
        <view class="res-det-list">
          <view v-for="(d, i) in record.detections" :key="i" class="res-det-item">
            <view class="res-det-badge"><text>{{ i + 1 }}</text></view>
            <view class="res-det-info">
              <text class="res-det-class">{{ d.class || '待确认' }}</text>
              <text class="res-det-sub">{{ d.severity || '' }} · 置信度 {{ ((d.confidence ?? 0) * 100).toFixed(0) }}%</text>
            </view>
          </view>
        </view>
      </view>

      <view class="res-done-btns">
        <button class="res-dbtn res-dbtn-primary" @tap="reupload">上传新影像</button>
        <button class="res-dbtn res-dbtn-outline" @tap="backToHome">返回首页</button>
      </view>
    </view>

    <!-- Error State -->
    <view v-if="pageState === 'error'" class="res-error">
      <text class="res-error-icon">😞</text>
      <text class="res-error-text">{{ errorMsg || '发生未知错误' }}</text>
      <view class="res-error-btns">
        <button class="res-ebtn res-ebtn-primary" @tap="reupload">再试一次</button>
        <button class="res-ebtn res-ebtn-outline" @tap="backToHome">返回首页</button>
      </view>
    </view>
  </view>
</template>

<style>
/* === Result Page === */
.res-page { min-height: 100vh; display: flex; flex-direction: column; }

/* Pick */
.res-pick {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; padding: 80px 40px 0;
}
.res-pick-icon { font-size: 96px; margin-bottom: 28px; }
.res-pick-title { font-size: 38px; font-weight: 700; color: #1e293b; display: block; }
.res-pick-desc { font-size: 26px; color: #94a3b8; text-align: center; margin-top: 12px; line-height: 1.6; display: block; }
.res-pick-types { display: flex; flex-direction: row; margin: 40px 0; }
.res-pick-type { display: flex; flex-direction: column; align-items: center; }
.res-pick-type-ml { margin-left: 20px; }
.res-type-icon { font-size: 44px; width: 80px; height: 80px; line-height: 80px; text-align: center; background: #f1f5f9; border-radius: 20px; }
.res-type-name { font-size: 22px; color: #64748b; margin-top: 8px; }
.res-pick-btn { width: 100%; height: 92px; line-height: 92px; text-align: center; background: #5b5fe3; color: #fff; border-radius: 16px; font-size: 32px; font-weight: 600; border: none; margin-top: 12px; }
.res-pick-tip { font-size: 22px; color: #cbd5e1; margin-top: 16px; display: block; }

/* Preview */
.res-preview { flex: 1; display: flex; flex-direction: column; padding: 24px 28px; }
.res-preview-label { font-size: 28px; font-weight: 600; color: #1e293b; margin-bottom: 16px; display: block; }
.res-preview-img { flex: 1; width: 100%; border-radius: 16px; background: #000; min-height: 500px; }
.res-preview-btns { display: flex; flex-direction: row; margin-top: 24px; }
.res-pvbtn { flex: 1; height: 88px; line-height: 88px; text-align: center; border-radius: 16px; font-size: 30px; font-weight: 600; border: none; }
.res-pvbtn-primary { background: #5b5fe3; color: #fff; margin-left: 16px; }
.res-pvbtn-outline { background: #f1f5f9; color: #334155; }

/* Uploading */
.res-uploading { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 120px 40px 0; }
.res-upload-icons { position: relative; margin-bottom: 32px; }
.res-upload-main { font-size: 80px; }
.res-upload-title { font-size: 36px; font-weight: 700; color: #1e293b; display: block; }
.res-upload-sub { font-size: 26px; color: #94a3b8; margin-top: 8px; display: block; }
.res-progress-wrap { width: 100%; margin-top: 40px; }
.res-progress-bar { width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
.res-progress-fill { height: 8px; background: linear-gradient(90deg, #5b5fe3, #818cf8); border-radius: 4px; }
.res-progress-pct { display: block; text-align: center; font-size: 24px; color: #5b5fe3; font-weight: 600; margin-top: 12px; }
.res-steps { display: flex; flex-direction: row; align-items: center; margin-top: 48px; width: 100%; }
.res-step { display: flex; flex-direction: column; align-items: center; }
.res-step-dot { width: 16px; height: 16px; border-radius: 8px; background: #e2e8f0; display: block; margin-bottom: 10px; }
.res-step-done .res-step-dot { background: #5b5fe3; }
.res-step-label { font-size: 20px; color: #cbd5e1; }
.res-step-done .res-step-label { color: #5b5fe3; font-weight: 600; }
.res-step-line { flex: 1; height: 2px; background: #e2e8f0; margin: 0 4px 20px 4px; }
.res-step-line-on { background: #a5b4fc; }

/* Done */
.res-done { padding: 24px 28px 48px; }
.res-done-status { display: flex; flex-direction: column; align-items: center; padding: 32px 0 24px; }
.res-done-icon { font-size: 64px; }
.res-done-status-text { font-size: 30px; font-weight: 600; color: #1e293b; margin-top: 12px; display: block; }
.res-report { background: #fff; border-radius: 20px; padding: 28px 24px; margin-bottom: 16px; }
.res-report-review { border-left: 4px solid #5b5fe3; }
.res-report-head { display: flex; flex-direction: row; justify-content: space-between; align-items: center; }
.res-report-title { font-size: 28px; font-weight: 600; color: #1e293b; }
.res-report-date { font-size: 22px; color: #94a3b8; }
.res-report-divider { height: 1px; background: #f1f5f9; margin: 18px 0; }
.res-report-content { font-size: 27px; color: #475569; line-height: 1.7; display: block; }
.res-det-list { display: flex; flex-direction: column; }
.res-det-item { display: flex; flex-direction: row; align-items: center; margin-bottom: 14px; }
.res-det-item:last-child { margin-bottom: 0; }
.res-det-badge { width: 40px; height: 40px; line-height: 40px; text-align: center; background: #f0f0ff; border-radius: 12px; flex-shrink: 0; font-size: 20px; font-weight: 700; color: #5b5fe3; margin-right: 14px; }
.res-det-info { flex: 1; }
.res-det-class { display: block; font-size: 26px; font-weight: 500; color: #1e293b; }
.res-det-sub { display: block; font-size: 22px; color: #94a3b8; margin-top: 2px; }
.res-done-btns { display: flex; flex-direction: column; margin-top: 24px; }
.res-dbtn { width: 100%; height: 92px; line-height: 92px; text-align: center; border-radius: 16px; font-size: 30px; font-weight: 600; border: none; margin-bottom: 14px; }
.res-dbtn:last-child { margin-bottom: 0; }
.res-dbtn-primary { background: #5b5fe3; color: #fff; }
.res-dbtn-outline { background: #f1f5f9; color: #334155; }

/* Error */
.res-error { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 160px 40px 0; }
.res-error-icon { font-size: 80px; }
.res-error-text { font-size: 28px; color: #64748b; margin-top: 16px; text-align: center; display: block; }
.res-error-btns { display: flex; flex-direction: column; width: 100%; margin-top: 32px; }
.res-ebtn { width: 100%; height: 92px; line-height: 92px; text-align: center; border-radius: 16px; font-size: 30px; font-weight: 600; border: none; margin-bottom: 14px; }
.res-ebtn:last-child { margin-bottom: 0; }
.res-ebtn-primary { background: #5b5fe3; color: #fff; }
.res-ebtn-outline { background: #f1f5f9; color: #334155; }
</style>
