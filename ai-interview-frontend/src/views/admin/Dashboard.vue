<template>
  <div>
    <h1 class="admin-page-title">&#x1F4CA; 数据概览</h1>
    <div class="stats-grid">
      <div class="stat-card" v-for="(s, i) in statCards" :key="i" :style="{ '--stat-accent': s.color, '--stat-accent-bg': s.bg }">
        <div class="stat-icon">{{ s.icon }}</div>
        <div class="stat-num">{{ stats[s.key] }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminUserApi } from '../../api/adminApi'

const stats = ref({ user_count: 0, resume_count: 0, interview_count: 0, completed_interview_count: 0 })

const statCards = [
  { key: 'user_count', label: '注册用户', icon: '👥', color: 'var(--c-primary)', bg: 'var(--c-primary-light)' },
  { key: 'resume_count', label: '上传简历', icon: '📄', color: 'var(--c-accent)', bg: 'var(--c-accent-light)' },
  { key: 'interview_count', label: '面试总数', icon: '🎤', color: '#2d7a4f', bg: '#f0fdf6' },
  { key: 'completed_interview_count', label: '已完成面试', icon: '✅', color: '#1e5a8a', bg: '#eff6ff' }
]

onMounted(async () => {
  try { stats.value = await adminUserApi.stats() } catch (e) { console.error(e) }
})
</script>

<style scoped>
.admin-page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-6);
}
</style>
