import Taro from '@tarojs/taro'
import { post } from './http'

export interface UserInfo {
  user_id: string
  username: string
  display_name: string
  role: string
  role_label: string
  permissions: string[]
}

export async function login(username: string, password: string) {
  const result = await post<{
    access_token: string
    token_type: string
    user: UserInfo
  }>('/api/v1/auth/login', { username, password })

  Taro.setStorageSync('access_token', result.access_token)
  Taro.setStorageSync('user', JSON.stringify(result.user))
  return result
}

export function getStoredUser(): UserInfo | null {
  const raw = Taro.getStorageSync('user')
  if (!raw) return null
  try { return JSON.parse(raw) } catch { return null }
}

export function isLoggedIn(): boolean {
  return !!Taro.getStorageSync('access_token')
}

export function logout() {
  Taro.removeStorageSync('access_token')
  Taro.removeStorageSync('user')
}
