<template>
  <AuthLayout>
    <template #title>注册</template>
    <template #subtitle>创建你的智面账号，开始 AI 模拟面试</template>

    <form @submit.prevent="handleRegister">
      <div class="form-row">
        <div class="form-group">
          <label>名</label>
          <input v-model="form.first_name" placeholder="名" required />
        </div>
        <div class="form-group">
          <label>姓</label>
          <input v-model="form.last_name" placeholder="姓" required />
        </div>
      </div>
      <div class="form-group">
        <label>邮箱</label>
        <input v-model="form.email" type="email" placeholder="请输入邮箱" required autocomplete="email" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <div class="password-wrapper">
          <input v-model="form.password" :type="showPw ? 'text' : 'password'" placeholder="至少6位，含字母和数字" required autocomplete="new-password" />
          <button type="button" class="password-toggle" @click="showPw = !showPw" tabindex="-1">
            {{ showPw ? '🙈' : '👁' }}
          </button>
        </div>
        <p v-if="form.password && pwStrength" class="form-hint" :style="{ color: pwStrengthColor }">
          密码强度：{{ pwStrength }}
        </p>
      </div>
      <p v-if="error" class="error-msg">{{ error }}</p>
      <p v-if="success" class="success-msg">{{ success }}</p>
      <button type="submit" class="btn-glow" :disabled="loading || !canSubmit">
        {{ loading ? '注册中...' : '注册' }}
      </button>
    </form>

    <template #footer>
      已有账号？<router-link to="/login">去登录</router-link>
    </template>
  </AuthLayout>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { register } from '../api/auth'
import AuthLayout from '../components/AuthLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const form = reactive({ first_name: '', last_name: '', email: '', password: '' })
const showPw = ref(false)
const error = ref('')
const success = ref('')
const loading = ref(false)

const canSubmit = computed(() =>
  form.first_name.trim() && form.last_name.trim() &&
  form.email.trim() && form.password.length >= 6
)

const pwStrength = computed(() => {
  const p = form.password
  if (p.length < 6) return '太短'
  const hasLetter = /[a-zA-Z]/.test(p)
  const hasDigit = /\d/.test(p)
  const hasSpecial = /[^a-zA-Z0-9]/.test(p)
  if (p.length >= 8 && hasLetter && hasDigit && hasSpecial) return '强'
  if (hasLetter && hasDigit) return '中等'
  return '弱'
})

const pwStrengthColor = computed(() => {
  const s = pwStrength.value
  if (s === '强') return 'var(--c-success)'
  if (s === '中等') return 'var(--c-warning)'
  return 'var(--c-danger)'
})

async function handleRegister() {
  error.value = ''; success.value = ''
  if (!form.first_name.trim()) { error.value = '请输入名'; return }
  if (!form.last_name.trim()) { error.value = '请输入姓'; return }
  if (!form.email.trim()) { error.value = '请输入邮箱'; return }
  if (form.password.length < 6) { error.value = '密码至少6位'; return }
  loading.value = true
  try {
    const res = await register(form)
    authStore.setAuth(res)
    success.value = '注册成功，正在跳转...'
    setTimeout(() => router.push('/dashboard'), 800)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-row { display: flex; gap: 12px; }
.success-msg {
  background: var(--c-success-light);
  color: var(--c-success);
  font-size: var(--text-sm);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-5);
  border-left: 3px solid var(--c-success);
}
</style>
