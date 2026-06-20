<template>
  <AuthLayout>
    <h2 class="auth-title">管理员登录</h2>
    <form @submit.prevent="handleLogin" class="auth-form">
      <div class="form-group">
        <label>邮箱</label>
        <input v-model="form.email" type="email" placeholder="请输入管理员邮箱" required />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="form.password" type="password" placeholder="请输入密码" required />
      </div>
      <button type="submit" class="btn-primary btn-block" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </form>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminAuthStore } from '../../stores/adminAuth'
import { useToastStore } from '../../stores/toast'
import AuthLayout from '../../components/AuthLayout.vue'
import adminApi from '../../api/adminRequest'

const router = useRouter()
const adminStore = useAdminAuthStore()
const toast = useToastStore()

const form = reactive({ email: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  if (!form.email || !form.password) {
    toast.warning('请填写邮箱和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await adminApi.post('/backoffice/auth/login', form)
    adminStore.setToken(data.access_token, data.refresh_token)
    toast.success('登录成功')
    router.push('/admin/dashboard')
  } catch (e) {
    toast.error('登录失败: ' + e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  text-align: center;
  margin-bottom: var(--space-6);
}
.auth-form { display: flex; flex-direction: column; gap: var(--space-4); }
.btn-block { width: 100%; }
</style>
