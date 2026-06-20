<template>
  <AuthLayout>
    <h2 class="auth-title">登录</h2>
    <form @submit.prevent="handleLogin" class="auth-form">
      <div class="form-group">
        <label>邮箱</label>
        <input v-model="form.email" type="email" placeholder="请输入邮箱" required />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="form.password" type="password" placeholder="请输入密码" required />
      </div>
      <div class="form-options">
        <label class="checkbox-label">
          <input type="checkbox" v-model="form.rememberMe" />
          <span>记住我</span>
        </label>
        <router-link to="/forgot-password" class="forgot-link">忘记密码？</router-link>
      </div>
      <button type="submit" class="btn-primary btn-block" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>
      <p class="auth-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
    </form>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { login } from '../api/auth'
import { useToastStore } from '../stores/toast'
import AuthLayout from '../components/AuthLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToastStore()

const form = reactive({
  email: '',
  password: '',
  rememberMe: false
})
const loading = ref(false)

async function handleLogin() {
  if (!form.email || !form.password) {
    toast.warning('请填写邮箱和密码')
    return
  }
  loading.value = true
  try {
    const data = await login(form.email, form.password, form.rememberMe)
    authStore.setToken(data.access_token, data.refresh_token)
    toast.success('登录成功')
    router.push('/dashboard')
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
.form-options {
  display: flex; justify-content: space-between; align-items: center;
  font-size: var(--text-sm);
}
.checkbox-label { display: flex; align-items: center; gap: var(--space-2); cursor: pointer; }
.forgot-link { color: var(--c-primary); text-decoration: none; }
.forgot-link:hover { text-decoration: underline; }
.btn-block { width: 100%; }
.auth-footer {
  text-align: center; font-size: var(--text-sm);
  color: var(--c-text-muted); margin-top: var(--space-4);
}
.auth-footer a { color: var(--c-primary); text-decoration: none; font-weight: 500; }
</style>
