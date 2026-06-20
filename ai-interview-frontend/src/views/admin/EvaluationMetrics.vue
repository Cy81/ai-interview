<template>
  <div>
    <div class="page-header">
      <h1 class="admin-page-title">评测指标</h1>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <input v-model="dateFrom" type="date" class="filter-input" @change="loadMetrics()" />
      <span class="filter-sep">至</span>
      <input v-model="dateTo" type="date" class="filter-input" @change="loadMetrics()" />
    </div>

    <!-- 汇总卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-value">{{ metrics.avg_score || 0 }}</div>
        <div class="stat-label">平均分</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ metrics.total_evaluations || 0 }}</div>
        <div class="stat-label">评估总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ topBucket }}</div>
        <div class="stat-label">最多分数段</div>
      </div>
    </div>

    <!-- 分数分布图 -->
    <div class="chart-card" v-if="hasDistribution">
      <h3>分数分布</h3>
      <div class="chart-container">
        <Bar :data="distributionChartData" :options="barOptions" />
      </div>
    </div>

    <!-- 分数分布表格 -->
    <div class="detail-card" v-if="hasDistribution">
      <h3>分数段明细</h3>
      <table>
        <thead>
          <tr>
            <th>分数段</th>
            <th>数量</th>
            <th>占比</th>
            <th>分布</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(count, bucket) in metrics.score_distribution" :key="bucket">
            <td>{{ bucket }} 分</td>
            <td class="num-cell">{{ count }}</td>
            <td class="num-cell">{{ getPercent(count) }}%</td>
            <td>
              <div class="bar-bg">
                <div class="bar-fill" :style="{ width: getPercent(count) + '%' }"></div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js'
import { getEvaluationMetrics } from '../../api/llmLogs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const metrics = ref({})
const dateFrom = ref('')
const dateTo = ref('')

const hasDistribution = computed(() => {
  const d = metrics.value.score_distribution || {}
  return Object.values(d).some(v => v > 0)
})

const topBucket = computed(() => {
  const d = metrics.value.score_distribution || {}
  let max = 0, top = '-'
  for (const [k, v] of Object.entries(d)) {
    if (v > max) { max = v; top = k + ' 分'; }
  }
  return top
})

const distributionChartData = computed(() => {
  const d = metrics.value.score_distribution || {}
  return {
    labels: Object.keys(d),
    datasets: [{
      label: '评估数量',
      data: Object.values(d),
      backgroundColor: '#2563EB',
      borderRadius: 4,
    }]
  }
})

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true, grid: { color: '#E2E8F0' } }, x: { grid: { display: false } } }
}

function getPercent(count) {
  const total = metrics.value.total_evaluations || 1
  return ((count / total) * 100).toFixed(1)
}

async function loadMetrics() {
  try {
    const params = {}
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    metrics.value = await getEvaluationMetrics(params)
  } catch (e) {
    console.error('加载评测指标失败:', e)
  }
}

onMounted(loadMetrics)
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-5); }
.filter-bar { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-5); }
.filter-input {
  padding: var(--space-2) var(--space-3); border: 1px solid var(--c-border);
  border-radius: var(--radius-sm); font-size: var(--text-sm); background: var(--c-surface);
}
.filter-sep { color: var(--c-text-muted); font-size: 13px; }

.stat-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); margin-bottom: var(--space-5); }
.stat-card {
  background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--radius-md);
  padding: var(--space-5); text-align: center;
}
.stat-value { font-size: 28px; font-weight: 700; font-family: var(--font-mono); color: var(--c-text); }
.stat-label { font-size: 12px; color: var(--c-text-muted); margin-top: var(--space-1); }

.chart-card {
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--radius-md); padding: var(--space-5); margin-bottom: var(--space-4);
}
.chart-card h3 { font-size: 14px; font-weight: 600; margin-bottom: var(--space-4); }
.chart-container { height: 260px; }

.detail-card {
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--radius-md); padding: var(--space-5); margin-bottom: var(--space-4);
}
.detail-card h3 { font-size: 14px; font-weight: 600; margin-bottom: var(--space-3); }
table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
th, td { padding: var(--space-3) var(--space-4); text-align: left; border-bottom: 1px solid var(--c-border-light); }
th { font-weight: 600; color: var(--c-text-secondary); font-size: var(--text-xs); }
.num-cell { font-family: var(--font-mono); font-variant-numeric: tabular-nums; text-align: right; }

.bar-bg { height: 6px; background: var(--c-border-light); border-radius: 3px; width: 100%; }
.bar-fill { height: 100%; background: var(--c-primary); border-radius: 3px; transition: width 0.3s; }

@media (max-width: 768px) {
  .stat-cards { grid-template-columns: 1fr; }
}
</style>
