<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const auth = useAuth()

const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function handleLogin() {
  error.value = ''
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  submitting.value = true
  try {
    await auth.login(username.value, password.value)
    router.replace('/')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">智</div>
        <h1>智齿 AI</h1>
        <p>牙齿影像智能诊断系统</p>
      </div>

      <el-form @submit.prevent="handleLogin" label-position="top" class="login-form">
        <el-alert
          v-if="error"
          :title="error"
          type="error"
          show-icon
          :closable="false"
          class="login-error"
        />

        <el-form-item label="用户名">
          <el-input
            v-model="username"
            placeholder="请输入用户名"
            :prefix-icon="null"
            size="large"
          />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            show-password
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          :loading="submitting"
          class="login-submit"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>

      <div class="login-hint">
        默认账号：admin / admin123
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 28px;
  font-weight: 700;
  border-radius: 12px;
  margin-bottom: 12px;
}

.login-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 4px;
}

.login-header p {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.login-form {
  margin-bottom: 16px;
}

.login-error {
  margin-bottom: 16px;
}

.login-submit {
  width: 100%;
  margin-top: 8px;
}

.login-hint {
  text-align: center;
  font-size: 12px;
  color: #c0c4cc;
}
</style>
