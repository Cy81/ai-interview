<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <span class="logo-mark">F</span>
        <div class="logo-text-group">
          <span class="logo-text">{{ projectName }}</span>
          <span class="sidebar-subtitle">后台管理</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/admin/dashboard" exact-active-class="active">
          <span class="nav-icon">&#x1F4CA;</span> 数据概览
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <span class="footer-email">{{ adminStore.adminEmail }}</span>
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAdminAuthStore } from '../../stores/adminAuth'
import { useRouter } from 'vue-router'

const adminStore = useAdminAuthStore()
const router = useRouter()
const projectName = import.meta.env.VITE_PROJECT_NAME || 'Framework'

function handleLogout() {
  adminStore.logout()
  router.push('/admin/login')
}
</script>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; }

.sidebar {
  width: 252px;
  background: var(--c-surface);
  color: var(--c-text);
  padding: var(--space-6) var(--space-4);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 1px solid var(--c-border-light);
  scrollbar-width: none;
}
.sidebar::-webkit-scrollbar { display: none; }

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-3) var(--space-6);
  border-bottom: 1px solid var(--c-border-light);
  margin-bottom: var(--space-5);
}

.logo-mark {
  width: 36px; height: 36px;
  border-radius: var(--radius-sm);
  background: var(--c-primary);
  color: white;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono);
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
}

.logo-text-group { display: flex; flex-direction: column; }

.logo-text {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 400;
  color: var(--c-text);
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.sidebar-subtitle {
  font-size: 11px;
  color: var(--c-text-muted);
  letter-spacing: 0.06em;
  font-weight: 500;
  text-transform: uppercase;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.sidebar-nav a {
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  color: var(--c-text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  transition: all var(--duration-fast) var(--ease-out);
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.sidebar-nav a:hover {
  background: var(--c-primary-light);
  color: var(--c-primary);
}

.sidebar-nav a.active {
  background: var(--c-primary);
  color: white;
  box-shadow: var(--shadow-md);
}
.sidebar-nav a.active .nav-icon { opacity: 1; }

.nav-icon { font-size: 15px; opacity: 0.7; transition: opacity var(--duration-fast); }

.sidebar-footer {
  font-size: var(--text-xs);
  color: var(--c-text-muted);
  border-top: 1px solid var(--c-border-light);
  padding-top: var(--space-4);
  margin-top: var(--space-2);
}
.footer-email { display: block; margin-bottom: var(--space-2); }

.logout-btn {
  display: block;
  width: 100%;
  margin-top: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: 500;
  background: var(--c-bg);
  color: var(--c-text-secondary);
  border: 1px solid var(--c-border);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.logout-btn:hover {
  background: var(--c-danger-light);
  color: var(--c-danger);
  border-color: var(--c-danger);
}

.main-content {
  margin-left: 252px;
  flex: 1;
  padding: var(--space-6) var(--space-8);
  background: var(--c-bg);
  min-height: 100vh;
}
</style>
