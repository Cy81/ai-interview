<template>
  <div>
    <div class="page-header">
      <h1 class="admin-page-title">LLM 调用日志</h1>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <select v-model="filters.call_type" @change="page = 1; loadLogs()" class="filter-select">
        <option value="">全部类型</option>
        <option value="generate_questions">生成题目</option>
        <option value="evaluate_answer">评估回答</option>
        <option value="evaluate_answer_stream">流式评估</option>
        <option value="generate_report">生成报告</option>
        <option value="parse_resume">解析简历</option>
        <option value="analyze_resume">分析简历</option>
      </select>
      <select v-model="filters.status" @change="page = 1; loadLogs()" class="filter-select">
        <option value="">全部状态</option>
        <option value="success">成功</option>
        <option value="error">失败</option>
      </select>
      <input v-model="filters.model_name" placeholder="模型名称" class="filter-input" @input="debounceLoad" />
      <input v-model="filters.interview_id" placeholder="面试 ID" class="filter-input" style="width:100px" @input="debounceLoad" />
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>时间</th>
            <th>调用类型</th>
            <th>模型</th>
            <th>Prompt</th>
            <th>Completion</th>
            <th>Total</th>
            <th>延迟</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td>{{ formatDate(log.created_at) }}</td>
            <td><span class="badge badge-blue">{{ typeMap[log.call_type] || log.call_type }}</span></td>
            <td class="model-cell">{{ log.model_name }}</td>
            <td class="num-cell">{{ log.prompt_tokens }}</td>
            <td class="num-cell">{{ log.completion_tokens }}</td>
            <td class="num-cell">{{ log.total_tokens }}</td>
            <td class="num-cell">{{ log.latency_ms }}ms</td>
            <td>
              <span :class="['badge', log.status === 'success' ? 'badge-green' : 'badge-red']">
                {{ log.status === 'success' ? '成功' : '失败' }}
              </span>
            </td>
            <td class="action-cell">
              <button class="btn-secondary btn-sm" @click="viewDetail(log.id)">详情</button>
            </td>
          </tr>
          <tr v-if="logs.length === 0">
            <td colspan="9" class="empty-cell">暂无数据</td>
          </tr>
        </tbody>
      </table>

      <div class="admin-pagination" v-if="total > perPage">
        <button class="btn-sm" :disabled="page <= 1" @click="page--; loadLogs()">上一页</button>
        <span>{{ page }} / {{ Math.ceil(total / perPage) }}</span>
        <button class="btn-sm" :disabled="page >= Math.ceil(total / perPage)" @click="page++; loadLogs()">下一页</button>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div class="modal-overlay" v-if="showModal" @click.self="showModal = false">
      <div class="modal-content modal-lg">
        <div class="modal-header">
          <h3>调用详情 #{{ detailLog?.id }}</h3>
          <button class="modal-close" @click="showModal = false">&times;</button>
        </div>
        <div class="modal-body" v-if="detailLog">
          <div class="detail-grid">
            <div class="detail-item">
              <label>调用类型</label>
              <span>{{ typeMap[detailLog.call_type] || detailLog.call_type }}</span>
            </div>
            <div class="detail-item">
              <label>模型</label>
              <span>{{ detailLog.model_name }}</span>
            </div>
            <div class="detail-item">
              <label>温度</label>
              <span>{{ detailLog.temperature }}</span>
            </div>
            <div class="detail-item">
              <label>延迟</label>
              <span>{{ detailLog.latency_ms }}ms</span>
            </div>
            <div class="detail-item">
              <label>Token 用量</label>
              <span>{{ detailLog.prompt_tokens }} / {{ detailLog.completion_tokens }} / {{ detailLog.total_tokens }}</span>
            </div>
            <div class="detail-item">
              <label>面试 ID</label>
              <span>{{ detailLog.interview_id || '-' }}</span>
            </div>
            <div class="detail-item">
              <label>题目序号</label>
              <span>{{ detailLog.question_index ?? '-' }}</span>
            </div>
            <div class="detail-item">
              <label>状态</label>
              <span :class="['badge', detailLog.status === 'success' ? 'badge-green' : 'badge-red']">
                {{ detailLog.status === 'success' ? '成功' : '失败' }}
              </span>
            </div>
          </div>

          <div class="detail-section">
            <h4>请求消息</h4>
            <div class="json-block">
              <pre>{{ formatJson(detailLog.request_messages) }}</pre>
            </div>
          </div>

          <div class="detail-section">
            <h4>响应内容</h4>
            <div class="response-block">
              <pre>{{ detailLog.response_content || '(无内容)' }}</pre>
            </div>
          </div>

          <div class="detail-section" v-if="detailLog.error_message">
            <h4>错误信息</h4>
            <div class="error-block">
              <pre>{{ detailLog.error_message }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listLogs, getLogDetail } from '../../api/llmLogs'

const logs = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 20
const showModal = ref(false)
const detailLog = ref(null)
let debounceTimer = null

const filters = ref({
  call_type: '',
  status: '',
  model_name: '',
  interview_id: '',
})

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

function debounceLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    loadLogs()
  }, 300)
}

async function loadLogs() {
  try {
    const params = { page: page.value, per_page: perPage }
    if (filters.value.call_type) params.call_type = filters.value.call_type
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.model_name) params.model_name = filters.value.model_name
    if (filters.value.interview_id) params.interview_id = filters.value.interview_id
    const data = await listLogs(params)
    logs.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    console.error('加载日志失败:', e)
  }
}

async function viewDetail(id) {
  try {
    detailLog.value = await getLogDetail(id)
    showModal.value = true
  } catch (e) {
    console.error('加载详情失败:', e)
  }
}

function formatJson(obj) {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

onMounted(loadLogs)
</script>

<style scoped>
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: var(--space-5);
}
.filter-bar {
  display: flex; gap: var(--space-3); margin-bottom: var(--space-5); flex-wrap: wrap;
}
.filter-select, .filter-input {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  background: var(--c-surface);
}
.filter-input { width: 160px; }

.table-container { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
th, td {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  border-bottom: 1px solid var(--c-border-light);
}
th { font-weight: 600; color: var(--c-text-secondary); font-size: var(--text-xs); text-transform: uppercase; letter-spacing: 0.04em; }
.model-cell { font-family: var(--font-mono); font-size: var(--text-xs); max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.num-cell { font-family: var(--font-mono); font-variant-numeric: tabular-nums; text-align: right; }
.empty-cell { text-align: center; color: var(--c-text-muted); padding: var(--space-8) !important; }

.badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }
.badge-blue { background: var(--c-primary-light); color: var(--c-primary); }
.badge-green { background: #ECFDF5; color: #059669; }
.badge-red { background: #FEF2F2; color: #DC2626; }

.btn-sm { padding: 4px 12px; font-size: 12px; }
.btn-secondary { background: var(--c-surface); border: 1px solid var(--c-border); color: var(--c-text); cursor: pointer; border-radius: var(--radius-sm); }

.admin-pagination { display: flex; align-items: center; justify-content: center; gap: var(--space-4); padding: var(--space-5) 0; }
.admin-pagination button { padding: 4px 12px; border: 1px solid var(--c-border); border-radius: var(--radius-sm); background: var(--c-surface); cursor: pointer; font-size: 12px; }
.admin-pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.admin-pagination span { font-size: 13px; color: var(--c-text-secondary); }

/* 弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: var(--c-surface); border-radius: var(--radius-md); border: 1px solid var(--c-border); box-shadow: var(--shadow-xl); max-height: 85vh; display: flex; flex-direction: column; }
.modal-lg { width: 720px; max-width: 90vw; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: var(--space-4) var(--space-5); border-bottom: 1px solid var(--c-border-light); }
.modal-header h3 { font-size: var(--text-base); font-weight: 600; }
.modal-close { background: none; border: none; font-size: 20px; cursor: pointer; color: var(--c-text-muted); }
.modal-body { padding: var(--space-5); overflow-y: auto; flex: 1; }

.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4); margin-bottom: var(--space-5); }
.detail-item label { display: block; font-size: 11px; color: var(--c-text-muted); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 2px; }
.detail-item span { font-size: var(--text-sm); }

.detail-section { margin-bottom: var(--space-5); }
.detail-section h4 { font-size: 13px; font-weight: 600; margin-bottom: var(--space-2); color: var(--c-text-secondary); }
.json-block, .response-block, .error-block {
  background: var(--c-bg); border: 1px solid var(--c-border-light); border-radius: var(--radius-sm);
  padding: var(--space-3); max-height: 300px; overflow-y: auto;
}
.json-block pre, .response-block pre, .error-block pre {
  margin: 0; font-family: var(--font-mono); font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-all;
}
.error-block { border-color: #FCA5A5; background: #FEF2F2; }
</style>
