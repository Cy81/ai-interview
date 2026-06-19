<template>
  <AuthLayout>
    <template #title>登录</template>
    <template #subtitle>欢迎回到智面，继续你的面试准备</template>

    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label>邮箱</label>
        <input v-model="email" type="email" placeholder="your@email.com" required autocomplete="email" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <div class="password-wrapper">
          <input v-model="password" :type="showPw ? 'text' : 'password'" placeholder="输入密码" required autocomplete="current-password" />
          <button type="button" class="password-toggle" @click="showPw = !showPw" tabindex="-1">
            {{ showPw ? '🙈' : '👁' }}
          </button>
        </div>
      </div>
      <p v-if="error" class="error-msg">{{ error }}</p>
      <button type="submit" class="btn-glow" :disabled="loading || !canSubmit">
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </form>

    <template #footer>
      还没有账号？<router-link to="/register">立即注册</router-link>
    </template>
  </AuthLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { login } from '../api/auth'
import { getProfile } from '../api/user'
import AuthLayout from '../components/AuthLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const email = ref('')
const password = ref('')
const showPw = ref(false)
const error = ref('')
const loading = ref(false)

const canSubmit = computed(() => email.value.trim() && password.value.length >= 6)

async function handleLogin() {
  error.value = ''
  if (!email.value.trim()) { error.value = '请输入邮箱'; return }
  if (password.value.length < 6) { error.value = '密码至少6位'; return }
  loading.value = true
  try {
    const data = await login(email.value, password.value)
    authStore.setAuth(data)
    try {
      const profile = await getProfile()
      authStore.setUserInfo(profile)
    } catch (_) {}
    router.push('/dashboard')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>
