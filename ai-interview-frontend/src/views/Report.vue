<template>
  <div class="container">
    <!-- 加载骨架屏 -->
    <div v-if="loading" class="report-skeleton">
      <div class="card skeleton-header-card">
        <div class="skeleton" style="width:96px;height:96px;border-radius:50%;flex-shrink:0"></div>
        <div style="flex:1">
          <div class="skeleton" style="height:28px;width:60%;margin-bottom:12px"></div>
          <div class="skeleton" style="height:16px;width:80%"></div>
        </div>
      </div>
      <div class="card" style="margin-top:var(--space-4)">
        <div class="skeleton" style="height:18px;width:40%;margin-bottom:var(--space-4)"></div>
        <div class="skeleton" style="height:60px;width:100%;margin-bottom:var(--space-2)"></div>
      </div>
      <div class="card" style="margin-top:var(--space-4)">
        <div class="skeleton" style="height:18px;width:30%;margin-bottom:var(--space-4)"></div>
        <div v-for="i in 3" :key="i" class="skeleton" style="height:40px;margin-bottom:var(--space-2)"></div>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="loadError" class="card empty-state error-card">
      <p class="empty-icon">&#x26A0;&#xFE0F;</p>
      <p class="empty-title">报告加载失败</p>
      <p class="empty-desc">{{ loadError }}</p>
      <div class="error-actions">
        <button class="btn-primary" @click="fetchReport">重新加载</button>
        <router-link to="/dashboard" class="btn-secondary">返回首页</router-link>
      </div>
    </div>

    <!-- 报告内容 -->
    <div v-else-if="report" class="report-content">
      <!-- 总分 -->
      <div class="card score-card">
        <div class="score-circle">
          <div class="score-ring">
            <span class="score-num">{{ data.overall_score }}</span>
            <span class="score-label">/10</span>
          </div>
        </div>
        <div class="score-info">
          <h2>面试评估报告</h2>
          <p class="hire-rec" v-if="report.hire_recommendation">
            {{ report.hire_recommendation }}
          </p>
        </div>
      </div>

      <!-- 总结 -->
      <div class="card section-card" v-if="report.summary">
        <h3 class="section-title">总体评价</h3>
        <p class="summary-text">{{ report.summary }}</p>
      </div>

      <!-- 优势 & 不足 -->
      <div class="two-col section-gap">
        <div class="card" v-if="report.strengths?.length">
          <h3 class="section-title text-success">优势</h3>
          <ul>
            <li v-for="(s, i) in report.strengths" :key="i">{{ s }}</li>
          </ul>
        </div>
        <div class="card" v-if="report.weaknesses?.length">
          <h3 class="section-title text-danger">不足</h3>
          <ul>
            <li v-for="(w, i) in report.weaknesses" :key="i">{{ w }}</li>
          </ul>
        </div>
      </div>

      <!-- 建议 -->
      <div class="card section-card" v-if="report.suggestions?.length">
        <h3 class="section-title">改进建议</h3>
        <ul>
          <li v-for="(s, i) in report.suggestions" :key="i">{{ s }}</li>
        </ul>
      </div>

      <!-- 各题得分 -->
      <div class="card section-card" v-if="report.question_scores?.length">
        <h3 class="section-title">各题得分</h3>
        <div v-for="(q, i) in report.question_scores" :key="i" class="q-score-item">
          <div class="q-score-header">
            <span class="q-index">Q{{ i + 1 }}</span>
            <span class="q-text">{{ q.question }}</span>
            <span class="q-score" :style="{ color: getScoreColor(q.score) }">
              {{ q.score }}
            </span>
          </div>
          <div class="q-bar">
            <div class="q-bar-fill" :style="{ width: (q.score * 10) + '%', background: getScoreColor(q.score) }"></div>
          </div>
        </div>
      </div>

      <!-- 操作 -->
      <div class="report-actions">
        <router-link to="/resume/upload" class="btn-primary action-btn">再来一次</router-link>
        <router-link to="/dashboard" class="btn-secondary action-btn">返回首页</router-link>
      </div>
    </div>

    <!-- 兜底 -->
    <div v-else class="card empty-state fallback-card">
      <p class="empty-icon">&#x1F4CB;</p>
      <p class="empty-title">暂无报告</p>
      <router-link to="/dashboard" class="btn-secondary" style="margin-top:var(--space-4);display:inline-block">返回首页</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getReport } from '../api/interview'
import { scoreColor } from '../utils/helpers'

const route = useRoute()
const interviewId = route.params.id
const data = ref(null)
const report = ref(null)
const loading = ref(true)
const loadError = ref('')

const getScoreColor = (s) => scoreColor(s)

async function fetchReport() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getReport(interviewId)
    data.value = res
    report.value = res.report || {}
  } catch (e) {
    loadError.value = e.message || '未知错误'
  } finally {
    loading.value = false
  }
}

onMounted(fetchReport)
</script>

<style scoped>
.report-skeleton { max-width: 700px; margin: var(--space-8) auto; }
.skeleton-header-card { display: flex; gap: var(--space-6); align-items: center; }

.error-card { max-width: 500px; margin: 60px auto; }
.error-actions { display: flex; gap: var(--space-3); justify-content: center; margin-top: var(--space-5); }

.report-content { max-width: 700px; margin: var(--space-8) auto; }

/* 总分卡片 */
.score-card {
  display: flex; align-items: center; gap: var(--space-8);
  background: var(--c-primary-light);
  border-color: rgba(37,99,235,0.1);
}
.score-circle {
  width: 100px; height: 100px; border-radius: 50%;
  background: var(--c-primary);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; padding: 3px;
  box-shadow: var(--shadow-md);
}
.score-ring {
  width: 100%; height: 100%; border-radius: 50%;
  background: var(--c-surface);
  display: flex; align-items: center; justify-content: center;
  flex-direction: column;
}
.score-num {
  font-family: var(--font-mono);
  font-size: 32px;
  font-weight: 600;
  color: var(--c-primary);
  letter-spacing: -0.03em;
  line-height: 1;
}
.score-label { font-family: var(--font-mono); font-size: 12px; color: var(--c-text-muted); font-weight: 400; }
.score-info h2 {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  margin-bottom: var(--space-1);
  letter-spacing: -0.02em;
}
.hire-rec { font-size: var(--text-base); color: var(--c-text-secondary); margin-top: var(--space-1); line-height: 1.6; }

/* 段落卡片 */
.section-card { margin-top: var(--space-4); }
.section-gap { margin-top: var(--space-4); }
.section-title {
  font-family: var(--font-display);
  margin-bottom: var(--space-4);
  font-size: var(--text-lg);
  font-weight: 400;
  letter-spacing: -0.01em;
  border-bottom: 2px solid var(--c-border-light);
  padding-bottom: var(--space-3);
}
.text-success { color: var(--c-success); }
.text-danger { color: var(--c-danger); }
.summary-text { font-size: var(--text-base); line-height: 1.85; color: var(--c-text); }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4); }
ul { list-style: none; padding: 0; }
ul li {
  font-size: var(--text-base); line-height: 1.85;
  padding-left: var(--space-5); position: relative;
}
ul li::before {
  content: ''; position: absolute; left: 0; top: 10px;
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--c-primary-muted);
}

/* 各题得分 */
.q-score-item { margin-bottom: var(--space-4); }
.q-score-item:last-child { margin-bottom: 0; }
.q-score-header {
  display: flex; align-items: center; gap: var(--space-3);
  margin-bottom: var(--space-2); font-size: var(--text-base);
}
.q-index {
  background: var(--c-primary-light); padding: 2px 12px;
  border-radius: var(--radius-sm); font-weight: 600;
  font-size: var(--text-xs); color: var(--c-primary);
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
}
.q-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--c-text-secondary); }
.q-score {
  font-family: var(--font-mono);
  font-weight: 600;
  font-size: var(--text-lg);
  letter-spacing: -0.02em;
}
.q-bar {
  height: 4px; background: var(--c-border-light);
  border-radius: 0; overflow: hidden;
}
.q-bar-fill {
  height: 100%; border-radius: 0;
  transition: width 0.6s var(--ease-out);
}

/* 操作区 */
.report-actions {
  text-align: center; margin-top: var(--space-8); margin-bottom: var(--space-12);
  display: flex; justify-content: center; gap: var(--space-3);
}
.action-btn {
  display: inline-block;
  padding: var(--space-3) var(--space-8);
  border-radius: var(--radius-sm);
  font-weight: 600;
  letter-spacing: 0.04em;
  font-family: var(--font-mono);
}

.fallback-card { max-width: 500px; margin: 60px auto; }

/* 入场动画 */
.report-content > * {
  animation: reportIn 0.5s var(--ease-out) both;
}
.report-content > *:nth-child(1) { animation-delay: 0s; }
.report-content > *:nth-child(2) { animation-delay: 0.08s; }
.report-content > *:nth-child(3) { animation-delay: 0.16s; }
.report-content > *:nth-child(4) { animation-delay: 0.24s; }
.report-content > *:nth-child(5) { animation-delay: 0.32s; }
.report-content > *:nth-child(6) { animation-delay: 0.40s; }
@keyframes reportIn { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 640px) {
  .two-col { grid-template-columns: 1fr; }
  .score-card { gap: var(--space-4); flex-direction: column; text-align: center; }
  .score-circle { width: 84px; height: 84px; }
  .score-num { font-size: 28px; }
  .report-actions { flex-direction: column; align-items: center; }
}
</style>
