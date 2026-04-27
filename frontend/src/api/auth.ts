import { http } from './http'
import type { AuthProfile, RbacModel } from '../types/auth'

export async function getAuthProfile() {
  const response = await http.get<{ code: number; data: AuthProfile }>('/api/v1/auth/me')
  return response.data.data
}

export async function getRbacModel() {
  const response = await http.get<{ code: number; data: RbacModel }>('/api/v1/auth/rbac-model')
  return response.data.data
}
