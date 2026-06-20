<template>
  <AuthLayout>
    <h2 class="auth-title">注册</h2>
    <form @submit.prevent="handleRegister" class="auth-form">
      <div class="form-row">
        <div class="form-group">
          <label>姓</label>
          <input v-model="form.last_name" placeholder="姓" required />
        </div>
        <div class="form-group">
          <label>名</label>
          <input v-model="form.first_name" placeholder="名" required />
        </div>
      </div>
      <div class="form-group">
        <label>邮箱</label>
        <input v-model="form.email" type="email" placeholder="请输入邮箱" required />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="form.password" type="password" placeholder="至少8位，含字母、数字和特殊字符" required />
      </div>
      <button type="submit" class="btn-primary btn-block" :disabled="loading">
        {{ loading ? '注册中...' : '注册' }}
      </button>
      <p class="auth-footer">
        已有账号？<router-link to="/login">立即登录</router-link>
      </p>
    </form>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { register } from '../api/auth'
import { useToastStore } from '../stores/toast'
import AuthLayout from '../components/AuthLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToastStore()

const form = reactive({
  first_name: '',
  last_name: '',
  email: '',
  password: ''
})
const loading = ref(false)

async function handleRegister() {
  if (!form.email || !form.password || !form.first_name || !form.last_name) {
    toast.warning('请填写所有必填字段')
    return
  }
  loading.value = true
  try {
    const data = await register(form)
    authStore.setToken(data.access_token, data.refresh_token)
    toast.success('注册成功')
    router.push('/dashboard')
  } catch (e) {
    toast.error('注册失败: ' + e.message)
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
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.btn-block { width: 100%; }
.auth-footer {
  text-align: center; font-size: var(--text-sm);
  color: var(--c-text-muted); margin-top: var(--space-4);
}
.auth-footer a { color: var(--c-primary); text-decoration: none; font-weight: 500; }
</style>
