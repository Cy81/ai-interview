<template>
  <div id="app-root">
    <nav class="navbar" v-if="showNavbar">
      <div class="nav-content">
        <router-link to="/dashboard" class="nav-logo">
          <span class="nav-logo-mark">Z</span>
          <span class="nav-logo-text">智面</span>
        </router-link>
        <button class="nav-toggle" @click="mobileMenuOpen = !mobileMenuOpen" aria-label="菜单">
          <span :class="['hamburger', { open: mobileMenuOpen }]"></span>
        </button>
        <div :class="['nav-links', { 'nav-open': mobileMenuOpen }]">
          <router-link to="/dashboard" @click="mobileMenuOpen = false">面试记录</router-link>
          <router-link to="/resume/upload" @click="mobileMenuOpen = false">上传简历</router-link>
          <router-link to="/profile" class="nav-user-link" @click="mobileMenuOpen = false">
            <img v-if="authStore.userAvatar && !avatarError" :src="authStore.userAvatar" class="nav-avatar" alt="头像" @error="avatarError = true" />
            <span v-else class="nav-avatar-placeholder">{{ userInitial }}</span>
            <span>{{ authStore.userName || '个人中心' }}</span>
          </router-link>
          <router-link to="/admin/login" class="nav-admin-link" @click="mobileMenuOpen = false">管理后台</router-link>
          <button class="nav-logout-btn" @click="logout">退出</button>
        </div>
      </div>
    </nav>
    <router-view />
    <ToastContainer />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from './stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { getProfile } from './api/user'
import ToastContainer from './components/ToastContainer.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const avatarError = ref(false)
const mobileMenuOpen = ref(false)

const userInitial = computed(() => {
  const name = authStore.userName || ''
  return name.charAt(0).toUpperCase() || 'U'
})

const showNavbar = computed(() => {
  return authStore.token && !route.path.startsWith('/admin')
})

onMounted(async () => {
  if (authStore.token) {
    try {
      const data = await getProfile()
      authStore.setUserInfo(data)
      avatarError.value = false
    } catch (e) {
      // Token may be expired, silently ignore
    }
  }
})

function logout() {
  authStore.logout()
  mobileMenuOpen.value = false
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  background: var(--c-surface);
  border-bottom: 2px solid var(--c-border);
  padding: 0 var(--space-6);
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-content {
  max-width: 920px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
}
.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none !important;
  color: var(--c-text) !important;
}
.nav-logo-mark {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  background: var(--c-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 15px;
}
.nav-logo-text {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 400;
  letter-spacing: -0.02em;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
}
.nav-links a {
  color: var(--c-text-secondary);
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  transition: all var(--duration-fast);
  font-weight: 500;
  text-decoration: none !important;
}
.nav-links a:hover {
  color: var(--c-text);
  background: rgba(15,23,42,0.04);
}
.nav-links a.router-link-exact-active {
  color: var(--c-primary);
  background: var(--c-primary-light);
  font-weight: 600;
}
.nav-user-link {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm) !important;
}
.nav-avatar {
  width: 26px; height: 26px; border-radius: 50%; object-fit: cover;
  border: 1px solid var(--c-border);
}
.nav-avatar-placeholder {
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--c-primary);
  color: white; display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 600;
  font-family: var(--font-mono);
}
.nav-admin-link {
  font-size: var(--text-xs) !important;
  padding: 4px 10px !important;
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--c-border) !important;
  color: var(--c-text-muted) !important;
  font-weight: 500 !important;
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
}
.nav-admin-link:hover {
  color: var(--c-primary) !important;
  border-color: var(--c-primary) !important;
  background: var(--c-primary-light) !important;
}
.nav-logout-btn {
  padding: 5px 12px;
  font-size: var(--text-sm);
  color: var(--c-text-muted);
  background: transparent;
  border: 1.5px solid transparent;
  border-radius: var(--radius-sm);
  font-weight: 500;
  transition: all var(--duration-fast);
}
.nav-logout-btn:hover {
  color: var(--c-danger);
  border-color: var(--c-danger);
  background: var(--c-danger-light);
}

/* Mobile hamburger */
.nav-toggle {
  display: none;
  background: none;
  border: none;
  padding: 10px;
  cursor: pointer;
}
.hamburger {
  display: block;
  width: 18px;
  height: 2px;
  background: var(--c-text);
  position: relative;
  transition: background 0.2s;
}
.hamburger::before,
.hamburger::after {
  content: '';
  position: absolute;
  left: 0;
  width: 18px;
  height: 2px;
  background: var(--c-text);
  transition: transform 0.2s;
}
.hamburger::before { top: -5px; }
.hamburger::after { top: 5px; }
.hamburger.open { background: transparent; }
.hamburger.open::before { transform: rotate(45deg) translate(3.5px, 3.5px); }
.hamburger.open::after { transform: rotate(-45deg) translate(3.5px, -3.5px); }

@media (max-width: 768px) {
  .nav-toggle { display: block; }
  .nav-links {
    display: none;
    position: absolute;
    top: 56px;
    left: 0;
    right: 0;
    background: var(--c-surface);
    border-bottom: 2px solid var(--c-border);
    flex-direction: column;
    padding: var(--space-3) var(--space-4);
    gap: 2px;
  }
  .nav-links.nav-open { display: flex; }
  .nav-links a { width: 100%; padding: 12px 14px; }
}
</style>
