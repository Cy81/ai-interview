<template>
  <div>
    <div class="page-header">
      <h1 class="admin-page-title">Token 统计</h1>
      <div class="period-selector">
        <button v-for="p in periods" :key="p.value" :class="['period-btn', { active: period === p.value }]"
          @click="period = p.value; loadStats()">{{ p.label }}</button>
      </div>
    </div>

    <!-- 汇总卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_tokens?.toLocaleString() || 0 }}</div>
        <div class="stat-label">总 Token</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_calls || 0 }}</div>
        <div class="stat-label">总调用次数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.avg_latency_ms || 0 }}ms</div>
        <div class="stat-label">平均延迟</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${{ costEstimate.total_cost?.toFixed(4) || '0.0000' }}</div>
        <div class="stat-label">预估成本</div>
      </div>
    </div>

    <!-- Token 趋势图 -->
    <div class="chart-card" v-if="stats.daily_breakdown?.length">
      <h3>每日 Token 使用趋势</h3>
      <div class="chart-container">
        <Bar :data="dailyChartData" :options="barOptions" />
      </div>
    </div>

    <!-- 按模型分布 -->
    <div class="chart-row" v-if="stats.by_model?.length">
      <div class="chart-card half">
        <h3>按模型分布</h3>
        <div class="chart-container">
          <Doughnut :data="modelChartData" :options="doughnutOptions" />
        </div>
      </div>
      <div class="chart-card half">
        <h3>按调用类型分布</h3>
        <div class="chart-container">
          <Doughnut :data="typeChartData" :options="doughnutOptions" />
        </div>
      </div>
    </div>

    <!-- 成本明细 -->
    <div class="detail-card" v-if="costEstimate.by_model?.length">
      <h3>成本明细</h3>
      <table>
        <thead>
          <tr>
            <th>模型</th>
            <th>Prompt Tokens</th>
            <th>Completion Tokens</th>
            <th>预估成本</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in costEstimate.by_model" :key="m.model_name">
            <td class="mono">{{ m.model_name }}</td>
            <td class="num-cell">{{ m.prompt_tokens.toLocaleString() }}</td>
            <td class="num-cell">{{ m.completion_tokens.toLocaleString() }}</td>
            <td class="num-cell">${{ m.estimated_cost.toFixed(4) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bar, Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend } from 'chart.js'
import { getTokenStats, getCostEstimate } from '../../api/llmLogs'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend)

const stats = ref({})
const costEstimate = ref({})
const period = ref('day')

const periods = [
  { label: '日', value: 'day' },
  { label: '周', value: 'week' },
  { label: '月', value: 'month' },
]

const COLORS = ['#2563EB', '#7C3AED', '#059669', '#D97706', '#DC2626', '#0891B2', '#4F46E5', '#DB2777']

const dailyChartData = computed(() => ({
  labels: (stats.value.daily_breakdown || []).map(d => d.date),
  datasets: [{
    label: 'Token 使用量',
    data: (stats.value.daily_breakdown || []).map(d => d.total_tokens),
    backgroundColor: '#2563EB',
    borderRadius: 4,
  }]
}))

const modelChartData = computed(() => ({
  labels: (stats.value.by_model || []).map(m => m.model_name),
  datasets: [{
    data: (stats.value.by_model || []).map(m => m.total_tokens),
    backgroundColor: COLORS.slice(0, (stats.value.by_model || []).length),
  }]
}))

const typeChartData = computed(() => ({
  labels: (stats.value.by_call_type || []).map(t => t.call_type),
  datasets: [{
    data: (stats.value.by_call_type || []).map(t => t.total_tokens),
    backgroundColor: COLORS.slice(0, (stats.value.by_call_type || []).length),
  }]
}))

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true, grid: { color: '#E2E8F0' } }, x: { grid: { display: false } } }
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom', labels: { padding: 12, font: { size: 11 } } } }
}

async function loadStats() {
  try {
    const params = { period: period.value }
    stats.value = await getTokenStats(params)
    costEstimate.value = await getCostEstimate(params)
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

onMounted(loadStats)
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-5); }
.period-selector { display: flex; gap: 4px; }
.period-btn {
  padding: 6px 16px; border: 1px solid var(--c-border); border-radius: var(--radius-sm);
  background: var(--c-surface); cursor: pointer; font-size: 13px; transition: all 0.15s;
}
.period-btn.active { background: var(--c-primary); color: white; border-color: var(--c-primary); }

.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-4); margin-bottom: var(--space-5); }
.stat-card {
  background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--radius-md);
  padding: var(--space-5); text-align: center;
}
.stat-value { font-size: 24px; font-weight: 700; font-family: var(--font-mono); color: var(--c-text); }
.stat-label { font-size: 12px; color: var(--c-text-muted); margin-top: var(--space-1); }

.chart-card {
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--radius-md); padding: var(--space-5); margin-bottom: var(--space-4);
}
.chart-card h3 { font-size: 14px; font-weight: 600; margin-bottom: var(--space-4); }
.chart-container { height: 280px; }

.chart-row { display: flex; gap: var(--space-4); margin-bottom: var(--space-4); }
.chart-card.half { flex: 1; margin-bottom: 0; }

.detail-card {
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--radius-md); padding: var(--space-5); margin-bottom: var(--space-4);
}
.detail-card h3 { font-size: 14px; font-weight: 600; margin-bottom: var(--space-3); }
table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
th, td { padding: var(--space-3) var(--space-4); text-align: left; border-bottom: 1px solid var(--c-border-light); }
th { font-weight: 600; color: var(--c-text-secondary); font-size: var(--text-xs); }
.mono { font-family: var(--font-mono); }
.num-cell { font-family: var(--font-mono); font-variant-numeric: tabular-nums; text-align: right; }

@media (max-width: 768px) {
  .stat-cards { grid-template-columns: 1fr 1fr; }
  .chart-row { flex-direction: column; }
}
</style>
