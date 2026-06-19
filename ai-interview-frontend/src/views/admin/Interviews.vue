<template>
  <div>
    <div class="page-header">
      <h1 class="admin-page-title">&#x1F3A4; 面试记录</h1>
      <select v-model="statusFilter" @change="page = 1; loadInterviews()" class="filter-select">
        <option value="">全部状态</option>
        <option value="in_progress">进行中</option>
        <option value="completed">已完成</option>
      </select>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户</th>
            <th>目标岗位</th>
            <th>难度</th>
            <th>题数</th>
            <th>得分</th>
            <th>状态</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in interviews" :key="i.id">
            <td>{{ i.id }}</td>
            <td>{{ i.user_email }}</td>
            <td>{{ i.target_position }}</td>
            <td>{{ diffMap[i.difficulty] || i.difficulty }}</td>
            <td>{{ i.total_questions }}</td>
            <td>
              <span v-if="i.overall_score" class="score-value" :class="scoreClass(i.overall_score)">
                {{ i.overall_score }}
              </span>
              <span v-else class="score-empty">-</span>
            </td>
            <td><span :class="['badge', i.status === 'completed' ? 'badge-green' : 'badge-yellow']">{{ i.status === 'completed' ? '已完成' : '进行中' }}</span></td>
            <td>{{ formatDate(i.created_at) }}</td>
            <td class="action-cell">
              <router-link :to="`/admin/interviews/${i.id}`" class="btn-primary btn-sm" style="color:white;text-decoration:none">详情</router-link>
              <button class="btn-danger btn-sm" @click="handleDelete(i.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="admin-pagination" v-if="total > perPage">
        <button class="btn-sm" :disabled="page <= 1" @click="page--; loadInterviews()">上一页</button>
        <span>{{ page }} / {{ Math.ceil(total / perPage) }}</span>
        <button class="btn-sm" :disabled="page >= Math.ceil(total / perPage)" @click="page++; loadInterviews()">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminInterviewApi } from '../../api/adminApi'

const interviews = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 20
const statusFilter = ref('')
const diffMap = { easy: '简单', medium: '中等', hard: '困难' }

function formatDate(str) {
  if (!str) return ''
  return new Date(str).toLocaleString('zh-CN')
}

function scoreClass(score) {
  if (score >= 7) return 'score-high'
  if (score >= 5) return 'score-mid'
  return 'score-low'
}

async function loadInterviews() {
  try {
    const data = await adminInterviewApi.list({ page: page.value, per_page: perPage, status: statusFilter.value || undefined })
    interviews.value = data.items
    total.value = data.total
  } catch (e) { console.error(e) }
}

async function handleDelete(id) {
  if (!confirm('确定要删除这条面试记录吗？')) return
  try {
    await adminInterviewApi.delete(id)
    await loadInterviews()
  } catch (e) { alert('删除失败: ' + e.message) }
}

onMounted(loadInterviews)
</script>

<style scoped>
.admin-page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  letter-spacing: -0.02em;
}
.filter-select {
  width: 140px;
  height: 40px;
  padding: 0 var(--space-4);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  background: var(--c-surface);
}
.score-value { font-weight: 700; font-variant-numeric: tabular-nums; }
.score-high { color: var(--c-success); }
.score-mid { color: var(--c-warning); }
.score-low { color: var(--c-danger); }
.score-empty { color: var(--c-text-muted); }
</style>
