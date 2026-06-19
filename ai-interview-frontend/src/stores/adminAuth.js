import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAdminAuthStore = defineStore('adminAuth', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const refreshToken = ref(localStorage.getItem('admin_refreshToken') || '')
  const adminEmail = ref(localStorage.getItem('admin_email') || '')
  const adminName = ref(localStorage.getItem('admin_name') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function login(email, password) {
    // 直接调用 backoffice 登录接口
    const res = await axios.post('/api/v1/backoffice/auth/login', { email, password })
    const data = res.data.data
    if (res.data.code !== 200) {
      throw new Error(res.data.message || '登录失败')
    }

    token.value = data.access_token
    refreshToken.value = data.refresh_token
    localStorage.setItem('admin_token', data.access_token)
    localStorage.setItem('admin_refreshToken', data.refresh_token)

    // 获取管理员信息
    try {
      const meRes = await axios.get('/api/v1/backoffice/auth/me', {
        headers: { Authorization: 'Bearer ' + data.access_token }
      })
      if (meRes.data.code === 200) {
        const me = meRes.data.data
        adminEmail.value = me.email || email
        adminName.value = ((me.last_name || '') + (me.first_name || '')).trim() || me.email || ''
        localStorage.setItem('admin_email', adminEmail.value)
        localStorage.setItem('admin_name', adminName.value)
      }
    } catch (e) {
      adminEmail.value = email
      localStorage.setItem('admin_email', email)
    }

    return data
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    adminEmail.value = ''
    adminName.value = ''
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_refreshToken')
    localStorage.removeItem('admin_email')
    localStorage.removeItem('admin_name')
  }

  return { token, refreshToken, adminEmail, adminName, isLoggedIn, login, logout }
})
