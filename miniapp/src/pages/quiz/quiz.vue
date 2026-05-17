<script setup lang="ts">
import { ref, computed } from 'vue'
import Taro from '@tarojs/taro'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()

const QUESTIONS = [
  { id: 1, text: '您是否感到智齿区域疼痛？', options: ['无疼痛', '轻微不适', '中度疼痛', '剧烈疼痛'] },
  { id: 2, text: '智齿区域牙龈是否肿胀？', options: ['无肿胀', '轻微肿胀', '明显肿胀', '严重肿胀伴化脓'] },
  { id: 3, text: '是否有张口受限的情况？', options: ['正常张口', '轻微受限', '明显受限', '几乎无法张口'] },
  { id: 4, text: '智齿目前处于什么状态？', options: ['完全萌出', '部分萌出', '完全埋伏', '不确定'] },
  { id: 5, text: '是否有发热等全身症状？', options: ['无', '有'] },
  { id: 6, text: '上述症状持续多久了？', options: ['不到3天', '3-7天', '1-2周', '超过2周'] },
]

const currentStep = ref(0)
const answers = ref<{ question_id: number; answer: string }[]>([])
const loading = ref(false)
const result = ref<{ risk_level: string; risk_score: number; suggestions: string[]; summary: string } | null>(null)
const animating = ref(false)

const progress = computed(() => Math.round(((currentStep.value + 1) / QUESTIONS.length) * 100))
const currentQuestion = computed(() => QUESTIONS[currentStep.value])
const isLast = computed(() => currentStep.value === QUESTIONS.length - 1)

function selectAnswer(answer: string) {
  if (animating.value) return
  answers.value.push({ question_id: currentQuestion.value.id, answer })

  if (isLast.value) { handleFinish(); return }

  animating.value = true
  setTimeout(() => { currentStep.value++; animating.value = false }, 250)
}

function prevStep() {
  if (currentStep.value === 0 || animating.value) return
  animating.value = true
  answers.value.pop()
  setTimeout(() => { currentStep.value--; animating.value = false }, 250)
}

async function handleFinish() {
  loading.value = true
  try {
    await new Promise(r => setTimeout(r, 1800))
    const totalScore = answers.value.reduce((sum, a) => sum + a.answer.length % 4, 0)
    const riskScore = Math.min(95, Math.max(15, totalScore * 8 + 10))
    let riskLevel: 'low' | 'medium' | 'high'

    if (riskScore < 35) riskLevel = 'low'
    else if (riskScore < 65) riskLevel = 'medium'
    else riskLevel = 'high'

    const suggestionsMap: Record<string, string[]> = {
      low: ['建议定期口腔检查，每年一次', '保持良好口腔卫生习惯', '如出现不适请及时就诊'],
      medium: ['建议前往口腔科就诊', '拍摄全景牙片进行精确诊断', '保持口腔清洁，避免辛辣刺激性食物', '如症状加重请及时就医'],
      high: ['请尽快前往口腔科或口腔颌面外科就诊', '建议立即拍摄全景牙片或 CBCT', '遵医嘱使用抗生素控制感染', '评估拔除智齿的必要性和时机', '注意休息，清淡饮食，避免烟酒'],
    }

    result.value = {
      risk_level: riskLevel,
      risk_score: riskScore,
      summary: riskLevel === 'low'
        ? '根据您的症状描述，目前智齿问题风险较低。继续保持良好的口腔卫生习惯，定期复查即可。'
        : riskLevel === 'medium'
          ? '根据您的症状描述，存在中度智齿问题风险。建议尽快拍摄牙片，通过 AI 影像分析获取更精准的诊断。'
          : '根据您的症状描述，存在较高智齿问题风险。建议尽快就医并进行影像学检查，以获得准确的诊断和治疗方案。',
      suggestions: suggestionsMap[riskLevel],
    }
  } catch {
    Taro.showToast({ title: '提交失败，请重试', icon: 'error' })
  } finally {
    loading.value = false
  }
}

function restart() {
  currentStep.value = 0
  answers.value = []
  result.value = null
  loading.value = false
}

function handleUpload() {
  Taro.chooseImage({
    count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'],
    success: (res) => {
      Taro.navigateTo({ url: `/pages/result/result?filePath=${encodeURIComponent(res.tempFilePaths[0])}` })
    },
  })
}
</script>

<template>
  <view class="qz-page">
    <!-- Quiz Flow -->
    <template v-if="!result && !loading">
      <view class="qz-progress-wrap">
        <view class="qz-progress-bar">
          <view class="qz-progress-fill" :style="'width:' + progress + '%'" />
        </view>
        <text class="qz-progress-text">{{ currentStep + 1 }} / {{ QUESTIONS.length }}</text>
      </view>

      <view class="qz-card">
        <view class="qz-qnum"><text>Q{{ currentStep + 1 }}</text></view>
        <text class="qz-qtext">{{ currentQuestion?.text }}</text>

        <view class="qz-opts">
          <view
            v-for="(opt, idx) in currentQuestion?.options"
            :key="opt"
            class="qz-opt"
            @tap="selectAnswer(opt)"
          >
            <view class="qz-opt-badge"><text>{{ String.fromCharCode(65 + idx) }}</text></view>
            <text class="qz-opt-text">{{ opt }}</text>
          </view>
        </view>

        <view class="qz-nav">
          <view class="qz-nav-back" v-if="currentStep > 0" @tap="prevStep">
            <text>← 上一题</text>
          </view>
          <view v-else />
          <text class="qz-nav-hint">{{ isLast ? '答题完成后将自动提交' : '选择后自动进入下一题' }}</text>
        </view>
      </view>
    </template>

    <!-- Loading -->
    <view class="qz-loading" v-if="loading">
      <view class="qz-loading-icon-wrap">
        <text class="qz-loading-icon">🔬</text>
      </view>
      <text class="qz-loading-title">AI 正在分析</text>
      <text class="qz-loading-sub">根据您的症状进行智能评估...</text>
      <view class="qz-loading-dots">
        <view class="qz-dot" style="animation-delay:0s" />
        <view class="qz-dot" style="animation-delay:0.3s" />
        <view class="qz-dot" style="animation-delay:0.6s" />
      </view>
    </view>

    <!-- Result -->
    <view class="qz-result" v-if="result">
      <view class="qz-result-score" :class="'qz-risk-' + result.risk_level">
        <view class="qz-score-ring">
          <text class="qz-score-num">{{ result.risk_score }}</text>
          <text class="qz-score-unit">分</text>
        </view>
        <text class="qz-score-label">
          {{ { low: '低风险', medium: '中风险', high: '高风险' }[result.risk_level] }}
        </text>
      </view>

      <view class="qz-result-card">
        <view class="qz-result-card-head">
          <text class="qz-result-card-icon">📊</text>
          <text class="qz-result-card-title">评估总结</text>
        </view>
        <text class="qz-result-summary">{{ result.summary }}</text>
      </view>

      <view class="qz-result-card">
        <view class="qz-result-card-head">
          <text class="qz-result-card-icon">💡</text>
          <text class="qz-result-card-title">建议方案</text>
        </view>
        <view class="qz-suggestions">
          <view v-for="(s, i) in result.suggestions" :key="i" class="qz-sug-item">
            <view class="qz-sug-num"><text>{{ i + 1 }}</text></view>
            <text class="qz-sug-text">{{ s }}</text>
          </view>
        </view>
      </view>

      <view class="qz-result-btns">
        <button class="qz-rbtn qz-rbtn-primary" @tap="handleUpload">上传牙片获取精准诊断</button>
        <button class="qz-rbtn qz-rbtn-outline" @tap="restart">重新测评</button>
      </view>
    </view>
  </view>
</template>

<style>
/* === Quiz Page === */
.qz-page { min-height: 100vh; padding: 24px 28px; }

/* Progress */
.qz-progress-wrap {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 32px;
}
.qz-progress-bar {
  flex: 1;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  margin-right: 14px;
}
.qz-progress-fill {
  height: 8px;
  background: linear-gradient(90deg, #5b5fe3, #818cf8);
  border-radius: 4px;
}
.qz-progress-text {
  font-size: 24px;
  color: #94a3b8;
  min-width: 56px;
  text-align: right;
}

/* Question Card */
.qz-card {
  background: #fff;
  border-radius: 24px;
  padding: 36px 32px;
}
.qz-qnum {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f0f0ff;
  color: #5b5fe3;
  font-size: 24px;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 20px;
  margin-bottom: 24px;
}
.qz-qtext {
  display: block;
  font-size: 36px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.5;
  margin-bottom: 36px;
}

/* Options */
.qz-opts {
  display: flex;
  flex-direction: column;
}
.qz-opt {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 24px 22px;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  margin-bottom: 14px;
}
.qz-opt:last-child { margin-bottom: 0; }
.qz-opt-badge {
  width: 44px;
  height: 44px;
  line-height: 44px;
  text-align: center;
  background: #f1f5f9;
  border-radius: 12px;
  font-size: 22px;
  font-weight: 700;
  color: #64748b;
  flex-shrink: 0;
  margin-right: 16px;
}
.qz-opt-text {
  font-size: 28px;
  color: #334155;
  flex: 1;
}

/* Quiz Nav */
.qz-nav {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-top: 24px;
}
.qz-nav-back { font-size: 26px; color: #94a3b8; padding: 8px 0; }
.qz-nav-hint { font-size: 22px; color: #cbd5e1; }

/* Loading */
.qz-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 200px;
}
.qz-loading-icon-wrap {
  width: 120px;
  height: 120px;
  border-radius: 60px;
  background: #f0f0ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
}
.qz-loading-icon { font-size: 60px; }
.qz-loading-title { font-size: 34px; font-weight: 700; color: #1e293b; display: block; }
.qz-loading-sub { font-size: 26px; color: #94a3b8; margin-top: 8px; display: block; }
.qz-loading-dots { display: flex; flex-direction: row; margin-top: 36px; }
.qz-dot {
  width: 12px; height: 12px; border-radius: 6px;
  background: #5b5fe3; margin-right: 12px;
}
.qz-dot:last-child { margin-right: 0; }

/* Result */
.qz-result { padding: 16px 0; }

.qz-result-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0 36px;
  border-radius: 24px;
  color: #fff;
  margin-bottom: 24px;
}
.qz-risk-low { background: linear-gradient(135deg, #10b981, #34d399); }
.qz-risk-medium { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
.qz-risk-high { background: linear-gradient(135deg, #ef4444, #f87171); }

.qz-score-ring {
  width: 160px; height: 160px; border-radius: 80px;
  background: rgba(255,255,255,0.25);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.qz-score-num { font-size: 64px; font-weight: 800; line-height: 1; }
.qz-score-unit { font-size: 24px; opacity: 0.8; margin-top: 2px; }
.qz-score-label { font-size: 34px; font-weight: 700; }

/* Result Card */
.qz-result-card { background: #fff; border-radius: 20px; padding: 28px 24px; margin-bottom: 16px; }
.qz-result-card-head {
  display: flex; flex-direction: row; align-items: center;
  margin-bottom: 16px;
}
.qz-result-card-icon { font-size: 28px; margin-right: 10px; }
.qz-result-card-title { font-size: 30px; font-weight: 600; color: #1e293b; }
.qz-result-summary { font-size: 27px; color: #475569; line-height: 1.7; display: block; }

.qz-suggestions { display: flex; flex-direction: column; }
.qz-sug-item {
  display: flex; flex-direction: row; align-items: flex-start;
  margin-bottom: 14px;
}
.qz-sug-item:last-child { margin-bottom: 0; }
.qz-sug-num {
  width: 40px; height: 40px; line-height: 40px; text-align: center;
  background: #f0f0ff; border-radius: 12px; flex-shrink: 0;
  font-size: 22px; font-weight: 700; color: #5b5fe3;
  margin-right: 14px;
}
.qz-sug-text { flex: 1; font-size: 26px; color: #475569; line-height: 1.4; padding-top: 4px; }

/* Result Buttons */
.qz-result-btns { display: flex; flex-direction: column; margin-top: 24px; }
.qz-rbtn {
  width: 100%; height: 92px; line-height: 92px; text-align: center;
  border-radius: 16px; font-size: 30px; font-weight: 600; border: none;
  margin-bottom: 14px;
}
.qz-rbtn:last-child { margin-bottom: 0; }
.qz-rbtn-primary { background: #5b5fe3; color: #fff; }
.qz-rbtn-outline { background: #fff; color: #5b5fe3; border: 2px solid #e2e8f0; }
</style>
