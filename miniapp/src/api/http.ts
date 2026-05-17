import Taro from '@tarojs/taro'

const BASE_URL = 'https://your-server.com'

function getToken(): string {
  return Taro.getStorageSync('access_token') || ''
}

async function request<T>(url: string, method: 'GET' | 'POST' = 'GET', data?: Record<string, unknown>): Promise<T> {
  const token = getToken()
  const header: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) header['Authorization'] = `Bearer ${token}`

  try {
    const res = await Taro.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header,
    })

    if (res.statusCode === 200 && res.data?.code === 200) {
      return res.data.data as T
    }

    if (res.statusCode === 401) {
      Taro.removeStorageSync('access_token')
      Taro.removeStorageSync('user')
      Taro.reLaunch({ url: '/pages/index/index' })
      throw new Error('登录已过期，请重新登录')
    }

    throw new Error(res.data?.detail || '请求失败')
  } catch (err: any) {
    if (err?.message && !err.statusCode) throw err
    throw new Error(err?.message || '网络请求失败')
  }
}

export function get<T>(url: string): Promise<T> {
  return request<T>(url, 'GET')
}

export function post<T>(url: string, data?: Record<string, unknown>): Promise<T> {
  return request<T>(url, 'POST', data)
}

export function upload(url: string, filePath: string, formData: Record<string, string>): Promise<{ image_id: string; status: string; message: string }> {
  return new Promise((resolve, reject) => {
    const token = getToken()
    Taro.uploadFile({
      url: `${BASE_URL}${url}`,
      filePath,
      name: 'file',
      formData,
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: (res) => {
        try {
          const result = JSON.parse(res.data) as { code: number; data: { image_id: string; status: string; message: string } }
          if (res.statusCode === 200 && result.code === 200) {
            resolve(result.data)
          } else {
            reject(new Error('上传失败'))
          }
        } catch {
          reject(new Error('解析响应失败'))
        }
      },
      fail: (err) => reject(err),
    })
  })
}
