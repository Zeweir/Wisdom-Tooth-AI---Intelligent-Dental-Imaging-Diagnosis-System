<script setup lang="ts">
import { ref, computed } from 'vue'
import Taro from '@tarojs/taro'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()

const username = ref('')
const password = ref('')
const errorMsg = ref('')
const showPassword = ref(false)
const submitting = ref(false)

const isFormValid = computed(() => username.value.trim() && password.value.trim())

async function handleLogin() {
  if (!isFormValid.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }

  submitting.value = true
  errorMsg.value = ''

  try {
    await auth.login(username.value, password.value)
    Taro.reLaunch({ url: '/pages/index/index' })
  } catch {
    errorMsg.value = '用户名或密码错误，请重试'
  } finally {
    submitting.value = false
  }
}

function goBack() {
  Taro.navigateBack({ delta: 1 })
}
</script>

<template>
  <view class="login-page">
    <!-- Background decoration -->
    <view class="login-bg">
      <view class="login-bg-circle login-bg-c1" />
      <view class="login-bg-circle login-bg-c2" />
      <view class="login-bg-circle login-bg-c3" />
    </view>

    <!-- Content -->
    <view class="login-body">
      <!-- Brand -->
      <view class="login-brand">
        <image class="login-logo" src="/static/logo.png" mode="aspectFit" />
        <text class="login-name">智齿 AI</text>
        <text class="login-tagline">牙齿影像智能诊断系统</text>
      </view>

      <!-- Form Card -->
      <view class="login-card">
        <text class="login-card-title">账号登录</text>
        <text class="login-card-sub">使用您的系统账号登录</text>

        <!-- Username -->
        <view class="login-field">
          <view class="login-field-icon">
            <view class="login-icon-user" />
          </view>
          <input
            v-model="username"
            class="login-input"
            type="text"
            placeholder="用户名"
            placeholder-class="login-placeholder"
            :focus="true"
            @confirm="handleLogin"
          />
        </view>

        <!-- Password -->
        <view class="login-field">
          <view class="login-field-icon">
            <view class="login-icon-lock" />
          </view>
          <input
            v-model="password"
            class="login-input"
            :type="showPassword ? 'text' : 'password'"
            placeholder="密码"
            placeholder-class="login-placeholder"
            @confirm="handleLogin"
          />
          <view class="login-eye" @tap="showPassword = !showPassword">
            <view class="login-eye-icon" :class="{ 'login-eye-off': !showPassword }" />
          </view>
        </view>

        <!-- Error -->
        <view class="login-error" v-if="errorMsg">
          <view class="login-error-dot" />
          <text>{{ errorMsg }}</text>
        </view>

        <!-- Submit -->
        <button
          class="login-btn"
          :class="{ 'login-btn-disabled': !isFormValid }"
          :disabled="!isFormValid || submitting"
          :loading="submitting"
          @tap="handleLogin"
        >
          <text v-if="!submitting">登 录</text>
          <text v-else>登录中...</text>
        </button>
      </view>

      <!-- Footer hints -->
      <view class="login-footer">
        <text class="login-footer-title">可用测试账号</text>
        <view class="login-accounts">
          <view class="login-acc-item">
            <view class="login-acc-dot login-acc-chief" />
            <text class="login-acc-text">admin / admin123</text>
            <text class="login-acc-role">· 主任医生</text>
          </view>
          <view class="login-acc-item">
            <view class="login-acc-dot login-acc-doctor" />
            <text class="login-acc-text">doctor / doctor123</text>
            <text class="login-acc-role">· 审核医生</text>
          </view>
          <view class="login-acc-item">
            <view class="login-acc-dot login-acc-tech" />
            <text class="login-acc-text">tech / tech123</text>
            <text class="login-acc-role">· 影像技师</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<style>
/* === Login Page === */
.login-page {
  min-height: 100vh;
  background: linear-gradient(160deg, #f0f0ff 0%, #f8fafc 40%, #f1f5f9 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Background decoration */
.login-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}
.login-bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
}
.login-bg-c1 {
  width: 500px;
  height: 500px;
  background: #5b5fe3;
  top: -200px;
  right: -180px;
}
.login-bg-c2 {
  width: 260px;
  height: 260px;
  background: #818cf8;
  top: 300px;
  left: -100px;
}
.login-bg-c3 {
  width: 180px;
  height: 180px;
  background: #5b5fe3;
  bottom: 180px;
  right: -60px;
}

/* Body */
.login-body {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 40px;
}

/* Brand */
.login-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 100px;
  padding-bottom: 48px;
}
.login-logo {
  width: 88px;
  height: 88px;
  border-radius: 22px;
  box-shadow: 0 8px 32px rgba(91, 95, 227, 0.18);
}
.login-name {
  font-size: 40px;
  font-weight: 800;
  color: #1e293b;
  margin-top: 20px;
  letter-spacing: 2px;
}
.login-tagline {
  font-size: 26px;
  color: #64748b;
  margin-top: 8px;
  letter-spacing: 1px;
}

/* Card */
.login-card {
  background: #fff;
  border-radius: 24px;
  padding: 40px 32px 32px;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.03);
}
.login-card-title {
  display: block;
  font-size: 34px;
  font-weight: 700;
  color: #1e293b;
  text-align: center;
}
.login-card-sub {
  display: block;
  font-size: 26px;
  color: #94a3b8;
  text-align: center;
  margin-top: 6px;
  margin-bottom: 36px;
}

/* Form Fields */
.login-field {
  display: flex;
  flex-direction: row;
  align-items: center;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  padding: 0 20px;
  height: 96px;
  margin-bottom: 20px;
  transition: border-color 0.2s ease;
}
.login-field:focus-within {
  border-color: #5b5fe3;
  background: #fff;
  box-shadow: 0 0 0 6px rgba(91, 95, 227, 0.06);
}
.login-field-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
}

/* User icon (CSS drawn) */
.login-icon-user {
  width: 22px;
  height: 22px;
  position: relative;
}
.login-icon-user::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 10px;
  height: 10px;
  border: 2px solid #94a3b8;
  border-radius: 50%;
}
.login-icon-user::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 18px;
  height: 9px;
  background: #94a3b8;
  border-radius: 9px 9px 0 0;
}
.login-field:focus-within .login-icon-user::before {
  border-color: #5b5fe3;
}
.login-field:focus-within .login-icon-user::after {
  background: #5b5fe3;
}

/* Lock icon (CSS drawn) */
.login-icon-lock {
  width: 20px;
  height: 22px;
  position: relative;
}
.login-icon-lock::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 12px;
  height: 7px;
  border: 2px solid #94a3b8;
  border-bottom: 0;
  border-radius: 6px 6px 0 0;
}
.login-icon-lock::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 18px;
  height: 13px;
  background: #94a3b8;
  border-radius: 3px;
}
.login-field:focus-within .login-icon-lock::before {
  border-color: #5b5fe3;
}
.login-field:focus-within .login-icon-lock::after {
  background: #5b5fe3;
}

.login-input {
  flex: 1;
  height: 100%;
  font-size: 28px;
  color: #1e293b;
  background: transparent;
  border: none;
  outline: none;
}

.login-placeholder {
  color: #94a3b8;
  font-size: 28px;
}
.login-eye {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.login-eye-icon {
  width: 20px;
  height: 20px;
  border: 2px solid #cbd5e1;
  border-radius: 50%;
  position: relative;
}
.login-eye-icon::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 6px;
  height: 6px;
  background: #cbd5e1;
  border-radius: 50%;
}
.login-eye-off {
  border-color: #e2e8f0;
}
.login-eye-off::after {
  background: #e2e8f0;
}

/* Error */
.login-error {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  padding: 14px 20px;
  background: #fef2f2;
  border-radius: 12px;
  font-size: 24px;
  color: #dc2626;
}
.login-error-dot {
  width: 8px;
  height: 8px;
  border-radius: 4px;
  background: #ef4444;
  margin-right: 10px;
  flex-shrink: 0;
}

/* Button */
.login-btn {
  width: 100%;
  height: 96px;
  line-height: 96px;
  text-align: center;
  background: #5b5fe3;
  color: #fff;
  border: none;
  border-radius: 16px;
  font-size: 32px;
  font-weight: 600;
  letter-spacing: 4px;
  transition: all 0.2s ease;
}
.login-btn:active {
  background: #4f46e5;
  transform: scale(0.98);
}
.login-btn-disabled {
  background: #c7d2fe;
  color: rgba(255,255,255,0.8);
}

/* Footer */
.login-footer {
  margin-top: 40px;
  padding: 0 8px;
}
.login-footer-title {
  display: block;
  font-size: 24px;
  color: #94a3b8;
  text-align: center;
  margin-bottom: 20px;
}
.login-accounts {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.login-acc-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 12px;
  padding: 14px 24px;
  background: rgba(255,255,255,0.7);
  border-radius: 12px;
}
.login-acc-dot {
  width: 8px;
  height: 8px;
  border-radius: 4px;
  margin-right: 12px;
  flex-shrink: 0;
}
.login-acc-chief { background: #818cf8; }
.login-acc-doctor { background: #34d399; }
.login-acc-tech { background: #fbbf24; }
.login-acc-text {
  font-size: 22px;
  color: #475569;
}
.login-acc-role {
  font-size: 20px;
  color: #94a3b8;
  margin-left: 4px;
}
</style>
