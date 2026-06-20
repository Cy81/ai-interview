import axios from 'axios'
import { useAdminAuthStore } from '../stores/adminAuth'
import router from '../router'

const adminApi = axios.create({
  baseURL: '/api/v1/backoffice',
  timeout: 60000
})

// 请求拦截器 - 注入 admin token
adminApi.interceptors.request.use(config => {
  const adminStore = useAdminAuthStore()
  if (adminStore.token) {
    config.headers.Authorization = `Bearer ${adminStore.token}`
  }
  return config
})

// 响应拦截器 - 解包 ApiResponse
adminApi.interceptors.response.use(
  response => {
    const data = response.data
    if (data.code === 200) {
      return data.data
    }
    return Promise.reject(new Error(data.message || '请求失败'))
  },
  error => {
    if (error.response?.status === 403 || error.response?.status === 401) {
      const adminStore = useAdminAuthStore()
      adminStore.logout()
      router.push('/admin/login')
    }
    const data = error.response?.data
    let msg = data?.message || error.message || '网络错误'
    if (data?.detail) {
      if (Array.isArray(data.detail)) {
        msg = data.detail.map(d => d.msg || d.message || JSON.stringify(d)).join('; ')
      } else if (typeof data.detail === 'string') {
        msg = data.detail
      }
    }
    return Promise.reject(new Error(msg))
  }
)

export default adminApi
