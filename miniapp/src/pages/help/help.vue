<script setup lang="ts">
import Taro from '@tarojs/taro'

interface GuideStep {
  icon: string
  title: string
  desc: string
}

const steps: GuideStep[] = [
  {
    icon: '1',
    title: '上传牙科影像',
    desc: '点击首页「AI 影像分析」按钮，从相册选择或直接拍摄全景片、根尖片或 CBCT 影像。支持 JPG、PNG 格式，建议影像清晰、曝光正常。',
  },
  {
    icon: '2',
    title: 'AI 自动检测',
    desc: '上传完成后，系统自动调用深度学习模型分析影像，检测智齿阻生、龋齿、根尖周炎、牙槽骨吸收等常见牙科病灶。分析通常在 1-2 分钟内完成。',
  },
  {
    icon: '3',
    title: '查看诊断报告',
    desc: 'AI 分析完成后生成结构化诊断报告，包含病灶位置、严重程度、置信度评分和处理建议。医生可在此基础上审核并确认报告。',
  },
  {
    icon: '4',
    title: '症状自测（可选）',
    desc: '如不便立即拍摄牙片，可使用「症状自测」功能。回答 6 道关于智齿症状的选择题，系统会给出初步风险评估和就医建议。',
  },
  {
    icon: '5',
    title: '报告审核与归档',
    desc: '审核医生可对 AI 报告进行复核，添加专业意见。主任医生可正式确认报告。每次审核操作均生成版本快照，支持历史追溯。',
  },
]

const faqs = [
  {
    q: '支持哪些类型的牙科影像？',
    a: '目前支持全景片（Panoramic）、根尖片（Periapical）和 CBCT 三种类型。上传时请确保影像清晰完整。',
  },
  {
    q: 'AI 分析的准确率如何？',
    a: 'AI 模型基于大量标注数据训练，对常见病灶的检出率较高。但所有 AI 结果仅供参考，最终诊断需由专业医生结合临床表现确认。',
  },
  {
    q: '如何注册账号？',
    a: '系统采用预置账号模式。请联系系统管理员获取账号。默认提供主任医生、审核医生、影像技师三种角色。',
  },
  {
    q: '我的数据安全吗？',
    a: '所有影像和报告数据均加密存储，使用 JWT 鉴权确保只有授权用户可访问。系统支持本地部署，数据完全由您掌控。',
  },
  {
    q: '症状自测的结果代表什么？',
    a: '症状自测仅作为初步风险评估参考，不能替代专业牙科诊断。评分越高表示需要就医的紧迫性越高，建议高分用户尽快拍摄牙片进行 AI 精准分析。',
  },
  {
    q: '报告可以导出吗？',
    a: '系统支持生成 PDF 格式的诊断报告，包含完整的检测结果和结构化诊疗建议，可下载或打印。',
  },
]

function goBack() {
  Taro.navigateBack()
}

function goUpload() {
  Taro.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      Taro.navigateTo({ url: `/pages/result/result?filePath=${encodeURIComponent(res.tempFilePaths[0])}` })
    },
  })
}
</script>

<template>
  <view class="help-page">
    <!-- Hero -->
    <view class="help-hero">
      <text class="help-hero-icon">📖</text>
      <text class="help-hero-title">使用帮助</text>
      <text class="help-hero-sub">快速了解智齿 AI 的核心功能与使用方法</text>
    </view>

    <!-- Guide Steps -->
    <view class="help-section">
      <text class="help-section-title">操作流程</text>
      <view class="help-steps">
        <view v-for="step in steps" :key="step.icon" class="help-step">
          <view class="help-step-line" v-if="step.icon !== '1'" />
          <view class="help-step-body">
            <view class="help-step-num-wrap">
              <view class="help-step-num">{{ step.icon }}</view>
            </view>
            <view class="help-step-content">
              <text class="help-step-title">{{ step.title }}</text>
              <text class="help-step-desc">{{ step.desc }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- Quick Start Button -->
    <view class="help-cta">
      <button class="help-cta-btn" @tap="goUpload">
        <text>开始使用 AI 影像分析 →</text>
      </button>
    </view>

    <!-- FAQ -->
    <view class="help-section">
      <text class="help-section-title">常见问题</text>
      <view class="help-faqs">
        <view v-for="(faq, idx) in faqs" :key="idx" class="help-faq">
          <view class="help-faq-q">
            <text class="help-faq-qmark">Q</text>
            <text class="help-faq-qtext">{{ faq.q }}</text>
          </view>
          <view class="help-faq-a">
            <text class="help-faq-amark">A</text>
            <text class="help-faq-atext">{{ faq.a }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Footer -->
    <view class="help-footer">
      <text class="help-footer-text">如有更多问题，请联系系统管理员</text>
    </view>
  </view>
</template>

<style>
/* === Help Page === */
.help-page {
  min-height: 100vh;
  padding-bottom: 60px;
}

/* Hero */
.help-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 56px 40px 40px;
  background: linear-gradient(160deg, #f0f0ff 0%, #f8fafc 100%);
}
.help-hero-icon {
  font-size: 72px;
  margin-bottom: 20px;
}
.help-hero-title {
  font-size: 40px;
  font-weight: 800;
  color: #1e293b;
  display: block;
}
.help-hero-sub {
  font-size: 26px;
  color: #64748b;
  margin-top: 10px;
  text-align: center;
  display: block;
  line-height: 1.5;
}

/* Section */
.help-section {
  padding: 36px 28px 0;
}
.help-section-title {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  display: block;
  margin-bottom: 24px;
}

/* Steps */
.help-steps {
  display: flex;
  flex-direction: column;
}
.help-step {
  position: relative;
}
.help-step-line {
  width: 2px;
  height: 32px;
  background: #e2e8f0;
  margin-left: 26px;
}
.help-step-body {
  display: flex;
  flex-direction: row;
  background: #fff;
  border-radius: 20px;
  padding: 28px 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  margin-bottom: 12px;
}
.help-step-num-wrap {
  flex-shrink: 0;
  margin-right: 20px;
}
.help-step-num {
  width: 54px;
  height: 54px;
  line-height: 54px;
  text-align: center;
  background: #5b5fe3;
  color: #fff;
  border-radius: 16px;
  font-size: 26px;
  font-weight: 700;
}
.help-step-content {
  flex: 1;
  padding-top: 2px;
}
.help-step-title {
  display: block;
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}
.help-step-desc {
  display: block;
  font-size: 25px;
  color: #64748b;
  line-height: 1.7;
}

/* CTA */
.help-cta {
  padding: 28px;
}
.help-cta-btn {
  width: 100%;
  height: 92px;
  line-height: 92px;
  text-align: center;
  background: linear-gradient(135deg, #5b5fe3, #818cf8);
  color: #fff;
  border-radius: 16px;
  font-size: 30px;
  font-weight: 600;
  border: none;
  box-shadow: 0 6px 24px rgba(91,95,227,0.25);
}

/* FAQ */
.help-faqs {
  display: flex;
  flex-direction: column;
}
.help-faq {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.help-faq-q {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  margin-bottom: 14px;
}
.help-faq-qmark {
  width: 36px;
  height: 36px;
  line-height: 36px;
  text-align: center;
  background: #5b5fe3;
  color: #fff;
  border-radius: 10px;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
  margin-right: 12px;
}
.help-faq-qtext {
  flex: 1;
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
  padding-top: 4px;
}
.help-faq-a {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  padding-top: 14px;
  border-top: 1px solid #f1f5f9;
}
.help-faq-amark {
  width: 36px;
  height: 36px;
  line-height: 36px;
  text-align: center;
  background: #ecfdf5;
  color: #10b981;
  border-radius: 10px;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
  margin-right: 12px;
}
.help-faq-atext {
  flex: 1;
  font-size: 25px;
  color: #475569;
  line-height: 1.7;
  padding-top: 4px;
}

/* Footer */
.help-footer {
  padding: 40px 28px;
  text-align: center;
}
.help-footer-text {
  font-size: 24px;
  color: #cbd5e1;
}
</style>
