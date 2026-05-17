<script setup lang="ts">
import Taro from '@tarojs/taro'

const features = [
  { icon: '🦷', title: 'AI 影像分析', desc: '基于深度学习模型自动检测智齿阻生、龋齿、根尖周炎、牙槽骨吸收等常见牙科病灶' },
  { icon: '📋', title: '结构化报告', desc: '自动生成包含病灶位置、严重程度、置信度评分和处理建议的专业诊断报告' },
  { icon: '📊', title: '审核流程', desc: '支持影像技师上传、审核医生复核、主任医生确认的完整审核体系' },
  { icon: '🔒', title: '安全可靠', desc: 'JWT 鉴权 + 三角色权限管控 + 审计日志追踪，满足医疗数据合规要求' },
  { icon: '📱', title: '多端使用', desc: 'Web 医生工作台 + 微信小程序，随时随地查看诊断结果' },
  { icon: '📄', title: 'PDF 导出', desc: '支持生成 PDF 格式诊断报告，可下载打印，便于归档和患者沟通' },
]
</script>

<template>
  <view class="about-page">
    <!-- Header -->
    <view class="about-hero">
      <image class="about-logo" src="/static/logo.png" mode="aspectFit" />
      <text class="about-name">智齿 AI</text>
      <text class="about-ver">v0.1.0</text>
      <text class="about-desc">牙齿影像智能诊断系统</text>
    </view>

    <!-- Intro -->
    <view class="about-card">
      <text class="about-card-text">
        智齿 AI 是一款面向牙科医生和影像技师的智能辅助诊断系统。
        通过深度学习技术自动分析全景片、根尖片和 CBCT 影像，
        快速检测常见牙科病灶并生成结构化诊断报告，帮助医生提升诊断效率和准确性。
      </text>
    </view>

    <!-- Features -->
    <view class="about-section">
      <text class="about-section-title">核心功能</text>
      <view class="about-features">
        <view v-for="f in features" :key="f.title" class="about-feat">
          <view class="about-feat-icon">
            <text>{{ f.icon }}</text>
          </view>
          <view class="about-feat-info">
            <text class="about-feat-title">{{ f.title }}</text>
            <text class="about-feat-desc">{{ f.desc }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Tech Stack -->
    <view class="about-section">
      <text class="about-section-title">技术栈</text>
      <view class="about-tech">
        <view class="about-tech-item">
          <text class="about-tech-label">前端</text>
          <text class="about-tech-val">Vue 3 + Taro + Element Plus</text>
        </view>
        <view class="about-tech-item">
          <text class="about-tech-label">后端</text>
          <text class="about-tech-val">FastAPI + SQLAlchemy + Celery</text>
        </view>
        <view class="about-tech-item">
          <text class="about-tech-label">AI 引擎</text>
          <text class="about-tech-val">YOLOv8 + Ollama 多模态</text>
        </view>
        <view class="about-tech-item">
          <text class="about-tech-label">存储</text>
          <text class="about-tech-val">PostgreSQL + MinIO</text>
        </view>
        <view class="about-tech-item" style="border-bottom:0">
          <text class="about-tech-label">部署</text>
          <text class="about-tech-val">Docker + Nginx</text>
        </view>
      </view>
    </view>

    <!-- Footer -->
    <view class="about-footer">
      <text class="about-footer-text">Wisdom Tooth AI — Intelligent Dental Imaging Diagnosis System</text>
      <text class="about-footer-copy">© 2026 Wisdom Tooth AI Team</text>
    </view>
  </view>
</template>

<style>
/* === About Page === */
.about-page {
  min-height: 100vh;
  padding-bottom: 60px;
}

/* Hero */
.about-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 56px 40px 40px;
  background: linear-gradient(160deg, #f0f0ff 0%, #f8fafc 100%);
}
.about-logo {
  width: 96px;
  height: 96px;
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(91,95,227,0.18);
}
.about-name {
  font-size: 44px;
  font-weight: 800;
  color: #1e293b;
  margin-top: 20px;
}
.about-ver {
  font-size: 22px;
  color: #5b5fe3;
  background: #f0f0ff;
  padding: 4px 14px;
  border-radius: 12px;
  margin-top: 8px;
}
.about-desc {
  font-size: 26px;
  color: #64748b;
  margin-top: 10px;
}

/* Intro Card */
.about-card {
  margin: -20px 28px 0;
  background: #fff;
  border-radius: 20px;
  padding: 28px 24px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.05);
  position: relative;
  z-index: 1;
}
.about-card-text {
  font-size: 26px;
  color: #475569;
  line-height: 1.8;
  text-align: center;
}

/* Section */
.about-section {
  padding: 36px 28px 0;
}
.about-section-title {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  display: block;
  margin-bottom: 20px;
}

/* Features */
.about-features {
  display: flex;
  flex-direction: column;
}
.about-feat {
  display: flex;
  flex-direction: row;
  background: #fff;
  border-radius: 16px;
  padding: 24px 20px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.about-feat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 18px;
  flex-shrink: 0;
  font-size: 28px;
  background: #f8fafc;
}
.about-feat-info {
  flex: 1;
}
.about-feat-title {
  display: block;
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
}
.about-feat-desc {
  display: block;
  font-size: 24px;
  color: #64748b;
  line-height: 1.6;
}

/* Tech Stack */
.about-tech {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
}
.about-tech-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 22px 24px;
  border-bottom: 1px solid #f8fafc;
}
.about-tech-label {
  font-size: 26px;
  color: #94a3b8;
  width: 100px;
  flex-shrink: 0;
}
.about-tech-val {
  font-size: 26px;
  color: #1e293b;
  font-weight: 500;
}

/* Footer */
.about-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 44px;
}
.about-footer-text {
  font-size: 22px;
  color: #cbd5e1;
}
.about-footer-copy {
  font-size: 20px;
  color: #e2e8f0;
  margin-top: 6px;
}
</style>
