import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import Taro from '@tarojs/taro'
import { post } from '../api/http'

export interface UserInfo {
  user_id: string
  username: string
  display_name: string
  role: string
  role_label: string
  permissions: string[]
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(Taro.getStorageSync('access_token') || '')
  const user = ref<UserInfo | null>(null)
  const loading = ref(false)
  const ready = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => user.value?.role ?? '')
  const displayName = computed(() => user.value?.display_name || user.value?.username || '未登录')
  const canUpload = computed(() => user.value?.permissions?.includes('upload:images') ?? false)

  function _loadCachedUser() {
    const raw = Taro.getStorageSync('user')
    if (raw) {
      try { user.value = JSON.parse(raw) } catch { /* ignore */ }
    }
  }

  async function init() {
    _loadCachedUser()
    if (token.value) {
      try {
        const profile = await Taro.request({
          url: `${getBaseUrl()}/api/v1/auth/me`,
          method: 'GET',
          header: { Authorization: `Bearer ${token.value}` },
        })
        if (profile.statusCode === 200 && profile.data?.code === 200) {
          const u = profile.data.data
          user.value = {
            user_id: u.user_id,
            username: u.username,
            display_name: u.display_name,
            role: u.role,
            role_label: u.role_label,
            permissions: u.permissions,
          }
          Taro.setStorageSync('user', JSON.stringify(user.value))
        }
      } catch {
        clearAuth()
      }
    }
    ready.value = true
  }

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const result = await post<{
        access_token: string
        token_type: string
        user: UserInfo
      }>('/api/v1/auth/login', { username, password })
      token.value = result.access_token
      user.value = result.user
      Taro.setStorageSync('access_token', result.access_token)
      Taro.setStorageSync('user', JSON.stringify(result.user))
      return result
    } finally {
      loading.value = false
    }
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    Taro.removeStorageSync('access_token')
    Taro.removeStorageSync('user')
  }

  function logout() {
    clearAuth()
    Taro.reLaunch({ url: '/pages/index/index' })
  }

  return { token, user, loading, ready, isLoggedIn, role, displayName, canUpload, init, login, logout, clearAuth }
})

function getBaseUrl(): string {
  return 'https://your-server.com'
}
