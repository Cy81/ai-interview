import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useAdminAuthStore } from '../stores/adminAuth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { auth: true } },
  { path: '/resume/upload', name: 'ResumeUpload', component: () => import('../views/ResumeUpload.vue'), meta: { auth: true } },
  { path: '/interview/:id', name: 'Interview', component: () => import('../views/Interview.vue'), meta: { auth: true } },
  { path: '/interview/:id/report', name: 'Report', component: () => import('../views/Report.vue'), meta: { auth: true } },
  { path: '/profile', name: 'Profile', component: () => import('../views/Profile.vue'), meta: { auth: true } },

  // 管理后台路由
  { path: '/admin/login', name: 'AdminLogin', component: () => import('../views/admin/AdminLogin.vue') },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { admin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('../views/admin/Dashboard.vue') },
      { path: 'users', name: 'AdminUsers', component: () => import('../views/admin/Users.vue') },
      { path: 'interviews', name: 'AdminInterviews', component: () => import('../views/admin/Interviews.vue') },
      { path: 'interviews/:id', name: 'AdminInterviewDetail', component: () => import('../views/admin/InterviewDetail.vue') },
      { path: 'llm-config', name: 'LLMConfig', component: () => import('../views/admin/LLMConfig.vue') },
      { path: 'llm-logs', name: 'LLMLogs', component: () => import('../views/admin/LLMLogs.vue') },
      { path: 'llm-logs/:id', name: 'LLMLogDetail', component: () => import('../views/admin/LLMLogDetail.vue') },
      { path: 'token-stats', name: 'TokenStats', component: () => import('../views/admin/TokenStats.vue') },
      { path: 'evaluation', name: 'EvaluationMetrics', component: () => import('../views/admin/EvaluationMetrics.vue') },
      { path: 'question-bank', name: 'QuestionBank', component: () => import('../views/admin/QuestionBank.vue') },
      { path: 'documents', name: 'Documents', component: () => import('../views/admin/DocumentManagement.vue') },
      { path: 'documents/:id', name: 'DocumentDetail', component: () => import('../views/admin/DocumentDetail.vue') },
      { path: 'position-templates', name: 'PositionTemplates', component: () => import('../views/admin/PositionTemplates.vue') },
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
