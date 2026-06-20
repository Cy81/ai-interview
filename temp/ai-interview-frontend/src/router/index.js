import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useAdminAuthStore } from '../stores/adminAuth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { auth: true } },

  // 管理后台路由
  { path: '/admin/login', name: 'AdminLogin', component: () => import('../views/admin/AdminLogin.vue') },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { admin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('../views/admin/Dashboard.vue') },
    ]
  },

  { path: '/', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const adminStore = useAdminAuthStore()

  // 管理后台路由守卫
  if (to.meta.admin && !adminStore.isLoggedIn) {
    next('/admin/login')
    return
  }

  // 客户端路由守卫
  if (to.meta.auth && !authStore.isLoggedIn) {
    next('/login')
    return
  }

  next()
})

export default router
