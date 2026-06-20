<template>
  <div v-if="log" class="log-detail">
    <div class="page-header">
      <div>
        <router-link to="/admin/llm-logs" class="back-link">&larr; 返回日志列表</router-link>
        <h1 class="admin-page-title">调用详情 #{{ log.id }}</h1>
      </div>
    </div>

    <div class="detail-card">
      <div class="detail-grid">
        <div class="detail-item">
          <label>调用类型</label>
          <span>{{ typeMap[log.call_type] || log.call_type }}</span>
        </div>
        <div class="detail-item">
          <label>模型</label>
          <span class="mono">{{ log.model_name }}</span>
        </div>
        <div class="detail-item">
          <label>温度</label>
          <span class="mono">{{ log.temperature }}</span>
        </div>
        <div class="detail-item">
          <label>延迟</label>
          <span class="mono">{{ log.latency_ms }}ms</span>
        </div>
        <div class="detail-item">
          <label>Token (Prompt / Completion / Total)</label>
          <span class="mono">{{ log.prompt_tokens }} / {{ log.completion_tokens }} / {{ log.total_tokens }}</span>
        </div>
        <div class="detail-item">
          <label>面试 ID</label>
          <span>{{ log.interview_id || '-' }}</span>
        </div>
        <div class="detail-item">
          <label>题目序号</label>
          <span>{{ log.question_index ?? '-' }}</span>
        </div>
        <div class="detail-item">
          <label>状态</label>
          <span :class="['badge', log.status === 'success' ? 'badge-green' : 'badge-red']">
            {{ log.status === 'success' ? '成功' : '失败' }}
          </span>
        </div>
        <div class="detail-item">
          <label>时间</label>
          <span>{{ formatDate(log.created_at) }}</span>
        </div>
      </div>
    </div>

    <div class="detail-card">
      <h3>请求消息</h3>
      <div class="json-block">
        <pre>{{ formatJson(log.request_messages) }}</pre>
      </div>
    </div>

    <div class="detail-card">
      <h3>响应内容</h3>
      <div class="response-block">
        <pre>{{ log.response_content || '(无内容)' }}</pre>
      </div>
    </div>

    <div class="detail-card" v-if="log.error_message">
      <h3>错误信息</h3>
      <div class="error-block">
        <pre>{{ log.error_message }}</pre>
      </div>
    </div>
  </div>
  <div v-else class="loading-state">加载中...</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getLogDetail } from '../../api/llmLogs'

const route = useRoute()
const log = ref(null)

const typeMap = {
  generate_questions: '生成题目',
  evaluate_answer: '评估回答',
  evaluate_answer_stream: '流式评估',
  generate_report: '生成报告',
  parse_resume: '解析简历',
  analyze_resume: '分析简历',
}

function formatDate(str) {
  if (!str) return ''
  return new Date(str).toLocaleString('zh-CN')
}

function formatJson(obj) {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

onMounted(async () => {
  try {
    log.value = await getLogDetail(route.params.id)
  } catch (e) {
    console.error('加载日志详情失败:', e)
  }
})
</script>

<style scoped>
.log-detail { max-width: 900px; }
.back-link {
  font-size: var(--text-sm); color: var(--c-primary); text-decoration: none;
  display: inline-block; margin-bottom: var(--space-2);
}
.back-link:hover { text-decoration: underline; }

.detail-card {
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--radius-md); padding: var(--space-5); margin-bottom: var(--space-4);
}
.detail-card h3 {
  font-size: 14px; font-weight: 600; margin-bottom: var(--space-3);
  color: var(--c-text-secondary);
}

.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4); }
.detail-item label {
  display: block; font-size: 11px; color: var(--c-text-muted);
  text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 2px;
}
.detail-item span { font-size: var(--text-sm); }
.mono { font-family: var(--font-mono); }

.badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }
.badge-green { background: #ECFDF5; color: #059669; }
.badge-red { background: #FEF2F2; color: #DC2626; }

.json-block, .response-block, .error-block {
  background: var(--c-bg); border: 1px solid var(--c-border-light);
  border-radius: var(--radius-sm); padding: var(--space-4);
  max-height: 500px; overflow-y: auto;
}
.json-block pre, .response-block pre, .error-block pre {
  margin: 0; font-family: var(--font-mono); font-size: 12px;
  line-height: 1.6; white-space: pre-wrap; word-break: break-all;
}
.error-block { border-color: #FCA5A5; background: #FEF2F2; }

.loading-state { text-align: center; padding: var(--space-8); color: var(--c-text-muted); }
</style>
