<template>
  <div class="admin-login-wrapper">
    <div class="login-card">
      <div class="login-brand">
        <span class="login-mark">Z</span>
        <h2>管理后台</h2>
        <p class="subtitle">智面 AI 面试平台管理系统</p>
      </div>

      <div class="form-group">
        <label>邮箱</label>
        <input v-model="email" type="email" placeholder="管理员邮箱" @keyup.enter="handleLogin" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="密码" @keyup.enter="handleLogin" />
      </div>

      <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

      <button class="btn-glow" @click="handleLogin" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <div class="back-link">
        <router-link to="/login">返回用户登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminAuthStore } from '../../stores/adminAuth'

const router = useRouter()
const adminStore = useAdminAuthStore()

const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  if (!email.value || !password.value) {
    errorMsg.value = '请输入邮箱和密码'
    return
  }
  loading.value = true
  try {
    await adminStore.login(email.value, password.value)
    router.push('/admin/dashboard')
  } catch (e) {
    errorMsg.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg);
  position: relative;
}
.admin-login-wrapper::before {
  content: '';
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse 600px 400px at 20% 30%, rgba(37,99,235,0.05) 0%, transparent 70%),
    radial-gradient(ellipse 500px 500px at 80% 70%, rgba(16,185,129,0.03) 0%, transparent 70%);
  pointer-events: none;
}
.login-card {
  background: var(--c-surface);
  border-radius: var(--radius-md);
  padding: var(--space-10);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--c-border);
  width: 100%;
  max-width: 420px;
  position: relative;
  z-index: 1;
  animation: authCardIn var(--duration-slow) var(--ease-out);
}
@keyframes authCardIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.login-brand {
  text-align: center;
  margin-bottom: var(--space-8);
}
.login-mark {
  display: inline-flex;
  width: 48px; height: 48px;
  border-radius: var(--radius-sm);
  background: var(--c-primary);
  color: white;
  align-items: center; justify-content: center;
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 600;
  margin-bottom: var(--space-4);
}
.login-card h2 {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  color: var(--c-text);
  letter-spacing: -0.02em;
  margin-bottom: var(--space-1);
}
.subtitle {
  color: var(--c-text-muted);
  font-size: var(--text-sm);
}
.back-link {
  text-align: center;
  margin-top: var(--space-6);
  font-size: var(--text-sm);
  color: var(--c-text-muted);
}
</style>
