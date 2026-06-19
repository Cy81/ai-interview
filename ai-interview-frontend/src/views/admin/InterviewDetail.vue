<template>
  <div>
    <div class="detail-header">
      <router-link to="/admin/interviews" class="back-link">&larr; 返回列表</router-link>
      <h1 class="admin-page-title">面试详情 #{{ interviewId }}</h1>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>

    <template v-else-if="detail">
      <!-- 基本信息 -->
      <div class="card info-card">
        <div class="info-grid">
          <div class="info-item"><span class="info-label">目标岗位</span><span class="info-value">{{ detail.target_position }}</span></div>
          <div class="info-item"><span class="info-label">难度</span><span class="info-value">{{ diffMap[detail.difficulty] || detail.difficulty }}</span></div>
          <div class="info-item"><span class="info-label">题数</span><span class="info-value">{{ detail.total_questions }}</span></div>
          <div class="info-item"><span class="info-label">综合得分</span><span class="info-value score-highlight">{{ detail.overall_score || '-' }}</span></div>
          <div class="info-item"><span class="info-label">状态</span><span :class="['badge', detail.status === 'completed' ? 'badge-green' : 'badge-yellow']">{{ detail.status === 'completed' ? '已完成' : '进行中' }}</span></div>
        </div>
      </div>

      <!-- 报告 -->
      <div class="card section-card" v-if="detail.report?.summary">
        <h3 class="section-title">&#x1F4DD; 评估报告</h3>
        <p class="report-summary">{{ detail.report.summary }}</p>
        <div class="report-cols" v-if="detail.report.strengths || detail.report.weaknesses">
          <div v-if="detail.report.strengths?.length">
            <h4 class="text-success">优势</h4>
            <ul><li v-for="s in detail.report.strengths" :key="s">{{ s }}</li></ul>
          </div>
          <div v-if="detail.report.weaknesses?.length">
            <h4 class="text-danger">不足</h4>
            <ul><li v-for="w in detail.report.weaknesses" :key="w">{{ w }}</li></ul>
          </div>
        </div>
      </div>

      <!-- 对话记录 -->
      <div class="card section-card">
        <h3 class="section-title">&#x1F4AC; 对话记录</h3>
        <div v-for="m in detail.messages" :key="m.id" :class="['msg', m.role]">
          <div class="msg-role">{{ m.role === 'interviewer' ? '&#x1F916; 面试官' : '&#x1F464; 候选人' }}</div>
          <div class="msg-content">{{ m.content }}</div>
          <div v-if="m.score" class="msg-score">
            评分: {{ m.score }}/10
            <span v-if="m.feedback"> | {{ m.feedback }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { adminInterviewApi } from '../../api/adminApi'

const route = useRoute()
const interviewId = route.params.id
const detail = ref(null)
const loading = ref(true)
const diffMap = { easy: '简单', medium: '中等', hard: '困难' }

onMounted(async () => {
  try {
    detail.value = await adminInterviewApi.detail(interviewId)
  } catch (e) { console.error(e) }
  finally { loading.value = false }
})
</script>

<style scoped>
.detail-header {
  display: flex; align-items: center; gap: var(--space-4); margin-bottom: var(--space-6);
}
.back-link {
  font-size: var(--text-sm); color: var(--c-text-muted); text-decoration: none;
  transition: color var(--duration-fast);
}
.back-link:hover { color: var(--c-primary); }
.admin-page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  letter-spacing: -0.02em;
}
.loading-state {
  text-align: center; padding: 60px; color: var(--c-text-muted); font-size: var(--text-base);
}
.info-card { margin-bottom: var(--space-4); }
.info-grid { display: flex; gap: var(--space-8); flex-wrap: wrap; }
.info-item { display: flex; flex-direction: column; gap: var(--space-1); }
.info-label { font-size: var(--text-xs); color: var(--c-text-muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; font-family: var(--font-mono); }
.info-value { font-size: var(--text-base); font-weight: 500; }
.score-highlight { font-weight: 600; color: var(--c-primary); font-family: var(--font-mono); }
.section-card { margin-bottom: var(--space-4); }
.section-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 400;
  margin-bottom: var(--space-4);
  letter-spacing: -0.01em;
}
.report-summary { font-size: var(--text-base); line-height: 1.85; margin-bottom: var(--space-4); }
.text-success { color: var(--c-success); margin-bottom: var(--space-2); font-size: var(--text-sm); font-weight: 600; }
.text-danger { color: var(--c-danger); margin-bottom: var(--space-2); font-size: var(--text-sm); font-weight: 600; }
.report-cols { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-5); }
.report-cols ul { list-style: none; padding: 0; }
.report-cols li {
  font-size: var(--text-sm); line-height: 1.85; padding-left: var(--space-4); position: relative;
}
.report-cols li::before {
  content: ''; position: absolute; left: 0; top: 10px;
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--c-primary-muted);
}
.msg {
  margin-bottom: var(--space-4); padding: var(--space-4);
  border-radius: var(--radius-md); border: 1px solid var(--c-border-light);
}
.msg.interviewer { background: var(--c-bg); }
.msg.candidate { background: var(--c-primary-light); border-color: rgba(37,99,235,0.1); }
.msg-role { font-size: var(--text-xs); font-weight: 600; color: var(--c-text-muted); margin-bottom: var(--space-2); text-transform: uppercase; letter-spacing: 0.04em; font-family: var(--font-mono); }
.msg-content { font-size: var(--text-sm); line-height: 1.75; }
.msg-score { margin-top: var(--space-2); font-size: var(--text-xs); color: var(--c-primary); font-weight: 600; font-family: var(--font-mono); }
@media (max-width: 640px) { .report-cols { grid-template-columns: 1fr; } }
</style>
