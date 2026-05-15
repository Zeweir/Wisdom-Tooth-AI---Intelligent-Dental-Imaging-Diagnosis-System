import { computed, ref } from 'vue'
import { getAuthProfile, getRbacModel, login as loginApi } from '../api/auth'
import { getStoredToken, setStoredToken } from '../api/http'
import type { AuthProfile, RbacModel, UserInfo } from '../types/auth'

const authReady = ref(false)
const isLoading = ref(false)
const user = ref<UserInfo | null>(null)
const authProfile = ref<AuthProfile | null>(null)
const rbacModel = ref<RbacModel | null>(null)

const isAuthenticated = computed(() => !!getStoredToken())

export function useAuth() {
  async function login(username: string, password: string) {
    isLoading.value = true
    try {
      const response = await loginApi(username, password)
      setStoredToken(response.access_token)
      user.value = response.user
      authReady.value = true
      return response
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    setStoredToken(null)
    user.value = null
    authProfile.value = null
    rbacModel.value = null
  }

  async function refreshAuthState() {
    const token = getStoredToken()
    if (!token) {
      authReady.value = true
      return
    }

    try {
      const [profile, model] = await Promise.all([
        getAuthProfile(),
        getRbacModel(),
      ])
      authProfile.value = profile
      rbacModel.value = model
      user.value = {
        user_id: profile.user_id,
        username: profile.username,
        display_name: profile.display_name,
        role: profile.role,
        role_label: profile.role_label,
        permissions: profile.permissions,
      }
      authReady.value = true
    } catch {
      logout()
      authReady.value = true
    }
  }

  return {
    authReady,
    isLoading,
    isAuthenticated,
    user,
    authProfile,
    rbacModel,
    login,
    logout,
    refreshAuthState,
  }
}
