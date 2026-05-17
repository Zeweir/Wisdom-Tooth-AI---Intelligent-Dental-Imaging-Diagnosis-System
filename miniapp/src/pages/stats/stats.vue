<script setup lang="ts">
import { ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()

interface StatData {
  total: number
  byType: { label: string; value: number; color: string }[]
  byStatus: { label: string; value: number; color: string }[]
  byFinding: { label: string; value: number; color: string }[]
  avgConfidence: number
  reviewedRate: number
}

const data = ref<StatData>({
  total: 128,
  byType: [
    { label: '全景片', value: 72, color: '#5b5fe3' },
    { label: '根尖片', value: 35, color: '#818cf8' },
    { label: 'CBCT', value: 21, color: '#c7d2fe' },
  ],
  byStatus: [
    { label: 'AI 生成', value: 48, color: '#3b82f6' },
    { label: '已审核', value: 42, color: '#10b981' },
    { label: '已归档', value: 38, color: '#6b7280' },
  ],
  byFinding: [
    { label: '智齿阻生', value: 45, color: '#ef4444' },
    { label: '龋齿', value: 38, color: '#f59e0b' },
    { label: '根尖周炎', value: 22, color: '#8b5cf6' },
    { label: '牙槽骨吸收', value: 18, color: '#06b6d4' },
    { label: '冠周炎', value: 12, color: '#f97316' },
  ],
  avgConfidence: 89.5,
  reviewedRate: 62.5,
})

const loading = ref(false)

useDidShow(async () => {
  await auth.init()
})

function getMaxValue(items: { value: number }[]) {
  return Math.max(...items.map(i => i.value), 1)
}

function getBarPercent(val: number, max: number) {
  return Math.round((val / max) * 100)
}

function getStatusDot(status: string) {
  const map: Record<string, string> = { 'AI 生成': '#3b82f6', '已审核': '#10b981', '已归档': '#6b7280' }
  return map[status] || '#94a3b8'
}
</script>

<template>
  <view class="st-page">
    <!-- Hero Summary -->
    <view class="st-hero">
      <text class="st-hero-label">总检测次数</text>
      <view class="st-hero-row">
        <text class="st-hero-num">{{ data.total }}</text>
        <text class="st-hero-unit">次</text>
      </view>
      <view class="st-hero-meta">
        <view class="st-hero-meta-item">
          <text class="st-meta-val">{{ data.avgConfidence }}%</text>
          <text class="st-meta-label">平均置信度</text>
        </view>
        <view class="st-hero-meta-div" />
        <view class="st-hero-meta-item">
          <text class="st-meta-val">{{ data.reviewedRate }}%</text>
          <text class="st-meta-label">审核完成率</text>
        </view>
      </view>
    </view>

    <!-- Image Type Distribution -->
    <view class="st-section">
      <text class="st-section-title">影像类型分布</text>
      <view class="st-card">
        <view class="st-type-chart">
          <!-- CSS Donut Chart -->
          <view class="st-donut">
            <view class="st-donut-inner">
              <text class="st-donut-num">{{ data.total }}</text>
              <text class="st-donut-sub">总计</text>
            </view>
          </view>
          <!-- Legend -->
          <view class="st-legend">
            <view v-for="t in data.byType" :key="t.label" class="st-legend-item">
              <view class="st-legend-dot" :style="{ background: t.color }" />
              <text class="st-legend-label">{{ t.label }}</text>
              <text class="st-legend-val">{{ t.value }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- Status Distribution -->
    <view class="st-section">
      <text class="st-section-title">审核状态分布</text>
      <view class="st-status-cards">
        <view v-for="s in data.byStatus" :key="s.label" class="st-status-card">
          <text class="st-status-num" :style="{ color: s.color }">{{ s.value }}</text>
          <text class="st-status-label">{{ s.label }}</text>
          <view class="st-status-bar-bg">
            <view
              class="st-status-bar-fill"
              :style="{ width: getBarPercent(s.value, getMaxValue(data.byStatus)) + '%', background: s.color }"
            />
          </view>
        </view>
      </view>
    </view>

    <!-- Findings Distribution -->
    <view class="st-section">
      <text class="st-section-title">病灶类型统计</text>
      <view class="st-card">
        <view class="st-findings">
          <view v-for="f in data.byFinding" :key="f.label" class="st-finding">
            <view class="st-finding-head">
              <view class="st-finding-dot" :style="{ background: f.color }" />
              <text class="st-finding-label">{{ f.label }}</text>
              <text class="st-finding-val">{{ f.value }}例</text>
            </view>
            <view class="st-finding-bar-bg">
              <view
                class="st-finding-bar-fill"
                :style="{ width: getBarPercent(f.value, getMaxValue(data.byFinding)) + '%', background: f.color }"
              />
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- Status Flow -->
    <view class="st-section">
      <text class="st-section-title">审核流转</text>
      <view class="st-flow">
        <view class="st-flow-item">
          <view class="st-flow-node st-flow-start" />
          <text class="st-flow-title">AI 分析</text>
          <text class="st-flow-num">{{ data.byStatus[0].value }} 份</text>
        </view>
        <view class="st-flow-arrow">→</view>
        <view class="st-flow-item">
          <view class="st-flow-node st-flow-mid" />
          <text class="st-flow-title">医生审核</text>
          <text class="st-flow-num">{{ data.byStatus[1].value }} 份</text>
        </view>
        <view class="st-flow-arrow">→</view>
        <view class="st-flow-item">
          <view class="st-flow-node st-flow-end" />
          <text class="st-flow-title">正式归档</text>
          <text class="st-flow-num">{{ data.byStatus[2].value }} 份</text>
        </view>
      </view>
      <text class="st-flow-hint">反映从 AI 初步分析到最终归档的审核流转情况</text>
    </view>

    <view class="st-bottom" />
  </view>
</template>

<style>
/* === Stats Page === */
.st-page {
  min-height: 100vh;
  padding-bottom: 60px;
}

/* Hero */
.st-hero {
  margin: 24px 28px;
  padding: 36px 32px;
  background: linear-gradient(135deg, #5b5fe3 0%, #7c3aed 100%);
  border-radius: 24px;
  color: #fff;
}
.st-hero-label {
  font-size: 24px;
  opacity: 0.8;
  display: block;
}
.st-hero-row {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  margin-top: 8px;
}
.st-hero-num {
  font-size: 64px;
  font-weight: 800;
  line-height: 1;
}
.st-hero-unit {
  font-size: 28px;
  opacity: 0.8;
  margin-left: 6px;
}
.st-hero-meta {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(255,255,255,0.2);
}
.st-hero-meta-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.st-hero-meta-div {
  width: 1px;
  height: 32px;
  background: rgba(255,255,255,0.25);
}
.st-meta-val {
  font-size: 32px;
  font-weight: 700;
}
.st-meta-label {
  font-size: 20px;
  opacity: 0.7;
  margin-top: 4px;
}

/* Section */
.st-section {
  padding: 12px 28px 0;
}
.st-section-title {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  display: block;
  margin-bottom: 16px;
}
.st-card {
  background: #fff;
  border-radius: 20px;
  padding: 28px 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* Type Chart */
.st-type-chart {
  display: flex;
  flex-direction: row;
  align-items: center;
}
.st-donut {
  width: 140px;
  height: 140px;
  border-radius: 70px;
  background: conic-gradient(#5b5fe3 0deg 203deg, #818cf8 203deg 301deg, #c7d2fe 301deg 360deg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 32px;
}
.st-donut-inner {
  width: 96px;
  height: 96px;
  border-radius: 48px;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.st-donut-num {
  font-size: 32px;
  font-weight: 800;
  color: #1e293b;
  line-height: 1.1;
}
.st-donut-sub {
  font-size: 20px;
  color: #94a3b8;
}
.st-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.st-legend-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 14px;
}
.st-legend-item:last-child { margin-bottom: 0; }
.st-legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  margin-right: 10px;
  flex-shrink: 0;
}
.st-legend-label {
  flex: 1;
  font-size: 26px;
  color: #475569;
}
.st-legend-val {
  font-size: 26px;
  font-weight: 600;
  color: #1e293b;
}

/* Status Cards */
.st-status-cards {
  display: flex;
  flex-direction: row;
}
.st-status-card {
  flex: 1;
  background: #fff;
  border-radius: 16px;
  padding: 24px 16px;
  margin-right: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  align-items: center;
}
.st-status-card:last-child { margin-right: 0; }
.st-status-num {
  font-size: 44px;
  font-weight: 800;
  line-height: 1;
}
.st-status-label {
  font-size: 22px;
  color: #64748b;
  margin-top: 8px;
  margin-bottom: 14px;
}
.st-status-bar-bg {
  width: 100%;
  height: 4px;
  background: #f1f5f9;
  border-radius: 2px;
  overflow: hidden;
}
.st-status-bar-fill {
  height: 4px;
  border-radius: 2px;
}

/* Findings */
.st-findings {
  display: flex;
  flex-direction: column;
}
.st-finding {
  margin-bottom: 20px;
}
.st-finding:last-child { margin-bottom: 0; }
.st-finding-head {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 10px;
}
.st-finding-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  margin-right: 8px;
  flex-shrink: 0;
}
.st-finding-label {
  flex: 1;
  font-size: 26px;
  color: #334155;
  font-weight: 500;
}
.st-finding-val {
  font-size: 24px;
  color: #94a3b8;
}
.st-finding-bar-bg {
  width: 100%;
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}
.st-finding-bar-fill {
  height: 8px;
  border-radius: 4px;
}

/* Flow */
.st-flow {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: center;
  padding: 32px 16px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.st-flow-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}
.st-flow-node {
  width: 16px;
  height: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
}
.st-flow-start { background: #3b82f6; }
.st-flow-mid { background: #10b981; }
.st-flow-end { background: #6b7280; }
.st-flow-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
}
.st-flow-num {
  font-size: 22px;
  color: #94a3b8;
  margin-top: 4px;
}
.st-flow-arrow {
  font-size: 32px;
  color: #cbd5e1;
  padding-top: 0;
  margin: 0 8px;
}
.st-flow-hint {
  display: block;
  text-align: center;
  font-size: 22px;
  color: #cbd5e1;
  margin-top: 12px;
}

.st-bottom { height: 24px; }
</style>
