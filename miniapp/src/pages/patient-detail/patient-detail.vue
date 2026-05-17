<script setup lang="ts">
import { ref } from 'vue'
import Taro, { useLoad } from '@tarojs/taro'
import { getPatient, getPatientImages, type PatientRecord } from '../../api/patients'
import type { DiagnosisRecord } from '../../api/diagnosis'
import StatusBadge from '../../components/StatusBadge.vue'

const patient = ref<PatientRecord | null>(null)
const images = ref<DiagnosisRecord[]>([])
const loading = ref(true)
const totalImages = ref(0)

useLoad(async (opts) => {
  const pid = opts?.patientId || ''
  if (!pid) return
  try {
    const [pRes, iRes] = await Promise.all([
      getPatient(pid),
      getPatientImages(pid, 20, 0),
    ])
    patient.value = pRes.data
    images.value = iRes.data
    totalImages.value = iRes.meta.total
  } catch { /* */ }
  finally { loading.value = false }
})

function goResult(imageId: string) {
  Taro.navigateTo({ url: `/pages/result/result?imageId=${imageId}` })
}

function uploadForPatient() {
  if (!patient.value) return
  Taro.chooseImage({
    count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'],
    success: (res) => {
      Taro.navigateTo({
        url: `/pages/result/result?filePath=${encodeURIComponent(res.tempFilePaths[0])}&patientId=${patient.value!.patient_id}`
      })
    },
  })
}

function getGenderLabel(g: string | null) {
  if (!g) return ''
  return g === '男' ? '♂' : '♀'
}

function formatDate(s: string | null) {
  if (!s) return ''
  return s.slice(0, 10).replace(/-/g, '/')
}

function formatDateTime(s: string) {
  if (!s) return ''
  return s.slice(0, 16).replace('T', ' ').replace(/-/g, '/')
}
</script>

<template>
  <view class="pd-page">
    <!-- Loading -->
    <view v-if="loading" class="pd-loading">
      <text class="pd-loading-text">加载中...</text>
    </view>

    <!-- Patient Info -->
    <view class="pd-hero" v-if="patient">
      <view class="pd-hero-bg" />
      <view class="pd-hero-card">
        <view class="pd-avatar">
          <text>{{ (patient.name || '?')[0] }}</text>
        </view>
        <text class="pd-name">{{ patient.name || patient.patient_id }}</text>

        <view class="pd-tags">
          <view class="pd-tag" v-if="patient.gender">
            <text :style="{ color: patient.gender === '男' ? '#3b82f6' : '#ec4899' }">
              {{ getGenderLabel(patient.gender) }} {{ patient.gender }}
            </text>
          </view>
          <view class="pd-tag" v-if="patient.age">
            <text>{{ patient.age }} 岁</text>
          </view>
          <view class="pd-tag">
            <text>{{ patient.image_count }} 次检查</text>
          </view>
        </view>

        <view class="pd-info-grid">
          <view class="pd-info-item">
            <text class="pd-info-label">患者ID</text>
            <text class="pd-info-val">{{ patient.patient_id }}</text>
          </view>
          <view class="pd-info-item" v-if="patient.phone">
            <text class="pd-info-label">手机号</text>
            <text class="pd-info-val">{{ patient.phone }}</text>
          </view>
          <view class="pd-info-item">
            <text class="pd-info-label">建档时间</text>
            <text class="pd-info-val">{{ formatDate(patient.created_at) }}</text>
          </view>
          <view class="pd-info-item">
            <text class="pd-info-label">最近检查</text>
            <text class="pd-info-val">{{ formatDate(patient.latest_image_at) || '无' }}</text>
          </view>
        </view>

        <view class="pd-notes" v-if="patient.notes">
          <text class="pd-notes-label">备注</text>
          <text class="pd-notes-text">{{ patient.notes }}</text>
        </view>
      </view>
    </view>

    <!-- Images Header -->
    <view class="pd-section" v-if="patient">
      <view class="pd-section-head">
        <text class="pd-section-title">影像记录 ({{ totalImages }})</text>
        <view class="pd-upload-btn" @tap="uploadForPatient">
          <text>+ 上传影像</text>
        </view>
      </view>
    </view>

    <!-- Image List -->
    <view class="pd-list" v-if="images.length > 0">
      <view
        v-for="img in images"
        :key="img.image_id"
        class="pd-img-item"
        @tap="goResult(img.image_id)"
      >
        <view class="pd-img-thumb">
          <text>🦷</text>
        </view>
        <view class="pd-img-info">
          <text class="pd-img-name">{{ img.filename || '牙科影像' }}</text>
          <text class="pd-img-meta">
            {{ img.image_type === 'panoramic' ? '全景片' : img.image_type === 'periapical' ? '根尖片' : img.image_type }}
            · {{ formatDateTime(img.created_at) }}
          </text>
        </view>
        <view class="pd-img-right">
          <StatusBadge :status="img.report.status" />
          <text class="pd-img-arrow">›</text>
        </view>
      </view>
    </view>

    <view class="pd-empty" v-if="!loading && images.length === 0 && patient">
      <text class="pd-empty-icon">📭</text>
      <text class="pd-empty-text">暂无影像记录</text>
    </view>
  </view>
</template>

<style>
/* === Patient Detail Page === */
.pd-page { min-height: 100vh; padding-bottom: 48px; }

.pd-loading { display: flex; justify-content: center; padding-top: 200px; }
.pd-loading-text { font-size: 28px; color: #94a3b8; }

/* Hero */
.pd-hero { padding: 24px 28px 0; position: relative; }
.pd-hero-bg {
  position: absolute; top: 0; left: 0; right: 0; height: 160px;
  background: linear-gradient(135deg, #5b5fe3 0%, #818cf8 100%);
  border-radius: 0 0 32px 32px;
}
.pd-hero-card {
  position: relative; background: #fff; border-radius: 24px;
  padding: 36px 28px 28px; display: flex; flex-direction: column;
  align-items: center; box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}
.pd-avatar {
  width: 80px; height: 80px; border-radius: 40px;
  background: linear-gradient(135deg, #5b5fe3, #818cf8);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 14px;
}
.pd-avatar text { font-size: 36px; font-weight: 700; color: #fff; }
.pd-name { font-size: 38px; font-weight: 700; color: #1e293b; display: block; }

.pd-tags {
  display: flex; flex-direction: row; flex-wrap: wrap;
  justify-content: center; margin-top: 12px;
}
.pd-tag {
  font-size: 22px; color: #475569; background: #f8fafc;
  padding: 6px 16px; border-radius: 12px; margin-right: 10px;
  margin-bottom: 6px;
}
.pd-tag:last-child { margin-right: 0; }

/* Info Grid */
.pd-info-grid {
  display: flex; flex-direction: row; flex-wrap: wrap;
  width: 100%; margin-top: 24px; padding-top: 20px;
  border-top: 1px solid #f1f5f9;
}
.pd-info-item {
  width: 50%; display: flex; flex-direction: column;
  margin-bottom: 16px;
}
.pd-info-label { font-size: 22px; color: #94a3b8; display: block; margin-bottom: 4px; }
.pd-info-val { font-size: 26px; color: #1e293b; font-weight: 500; display: block; }

.pd-notes { width: 100%; padding-top: 16px; border-top: 1px solid #f1f5f9; }
.pd-notes-label { font-size: 22px; color: #94a3b8; display: block; margin-bottom: 6px; }
.pd-notes-text { font-size: 25px; color: #475569; line-height: 1.6; display: block; }

/* Section */
.pd-section { padding: 28px 28px 0; }
.pd-section-head {
  display: flex; flex-direction: row; align-items: center;
  justify-content: space-between;
}
.pd-section-title { font-size: 32px; font-weight: 700; color: #1e293b; }
.pd-upload-btn {
  padding: 12px 24px; background: #5b5fe3; border-radius: 20px;
  font-size: 24px; color: #fff; font-weight: 500;
}

/* Image List */
.pd-list { padding: 16px 28px 0; display: flex; flex-direction: column; }
.pd-img-item {
  display: flex; flex-direction: row; align-items: center;
  background: #fff; border-radius: 16px; padding: 20px;
  margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.pd-img-thumb {
  width: 56px; height: 56px; border-radius: 14px;
  background: #f0f0ff; display: flex; align-items: center;
  justify-content: center; font-size: 28px; margin-right: 14px; flex-shrink: 0;
}
.pd-img-info { flex: 1; min-width: 0; }
.pd-img-name { display: block; font-size: 26px; font-weight: 500; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pd-img-meta { display: block; font-size: 22px; color: #94a3b8; margin-top: 4px; }
.pd-img-right { display: flex; flex-direction: row; align-items: center; flex-shrink: 0; }
.pd-img-arrow { font-size: 28px; color: #cbd5e1; margin-left: 10px; }

.pd-empty { display: flex; flex-direction: column; align-items: center; padding-top: 80px; }
.pd-empty-icon { font-size: 64px; margin-bottom: 16px; }
.pd-empty-text { font-size: 28px; color: #94a3b8; }
</style>
