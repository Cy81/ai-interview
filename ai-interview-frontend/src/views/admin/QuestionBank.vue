<template>
  <div>
    <div class="page-header">
      <h1 class="admin-page-title">&#x1F4DA; 题库管理</h1>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card" v-for="(s, i) in statCards" :key="i" :style="{ '--stat-accent': s.color, '--stat-accent-bg': s.bg }">
        <div class="stat-icon">{{ s.icon }}</div>
        <div class="stat-num">{{ stats[s.key] ?? 0 }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <input v-model="filters.keyword" placeholder="搜索题目关键词..." @input="debouncedSearch" />
      <select v-model="filters.category" @change="page = 1; loadList()">
        <option value="">全部分类</option>
        <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
      </select>
      <select v-model="filters.difficulty" @change="page = 1; loadList()">
        <option value="">全部难度</option>
        <option value="easy">简单</option>
        <option value="medium">中等</option>
        <option value="hard">困难</option>
      </select>
      <select v-model="filters.is_enabled" @change="page = 1; loadList()">
        <option value="">全部状态</option>
        <option :value="true">已启用</option>
        <option :value="false">已禁用</option>
      </select>
    </div>

    <!-- Action Buttons -->
    <div class="action-bar">
      <button class="btn-secondary" @click="showTestPanel = true">&#x1F50D; 检索测试</button>
      <button class="btn-secondary" @click="showImportModal = true">&#x1F4E5; 批量导入</button>
      <button class="btn-secondary" @click="handleReindexAll">&#x1F504; 全量重建</button>
      <button class="btn-primary" @click="openCreateModal">＋ 新增题目</button>
    </div>

    <!-- Table -->
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>分类</th>
            <th>岗位</th>
            <th>难度</th>
            <th>题面</th>
            <th>使用次数</th>
            <th>向量化</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.category }}</td>
            <td>{{ item.position_tag || '-' }}</td>
            <td>
              <span :class="['badge', diffBadge(item.difficulty)]">{{ diffMap[item.difficulty] || item.difficulty }}</span>
            </td>
            <td :title="item.question">{{ truncate(item.question, 60) }}</td>
            <td>{{ item.usage_count ?? 0 }}</td>
            <td>{{ item.is_vectorized ? '&#x2713;' : '&#x2717;' }}</td>
            <td>
              <span :class="['badge', item.is_enabled ? 'badge-green' : 'badge-red']">
                {{ item.is_enabled ? '启用' : '禁用' }}
              </span>
            </td>
            <td class="action-cell">
              <button class="btn-primary btn-sm" @click="openEditModal(item)">编辑</button>
              <button :class="item.is_enabled ? 'btn-danger btn-sm' : 'btn-primary btn-sm'" @click="handleToggle(item)">
                {{ item.is_enabled ? '禁用' : '启用' }}
              </button>
              <button class="btn-danger btn-sm" @click="handleDelete(item)">删除</button>
            </td>
          </tr>
          <tr v-if="list.length === 0">
            <td colspan="9" class="empty-row">暂无数据</td>
          </tr>
        </tbody>
      </table>

      <div class="admin-pagination" v-if="total > perPage">
        <button class="btn-sm" :disabled="page <= 1" @click="page--; loadList()">上一页</button>
        <span>{{ page }} / {{ Math.ceil(total / perPage) }}</span>
        <button class="btn-sm" :disabled="page >= Math.ceil(total / perPage)" @click="page++; loadList()">下一页</button>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showFormModal" class="admin-modal-overlay" @click.self="showFormModal = false">
      <div class="admin-modal">
        <div class="admin-modal-header">
          <h3>{{ editingId ? '编辑题目' : '新增题目' }}</h3>
          <button @click="showFormModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>分类</label>
          <select v-model="form.category">
            <option value="" disabled>请选择分类</option>
            <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>岗位标签</label>
          <input v-model="form.position_tag" placeholder="如：前端、后端、算法" />
        </div>
        <div class="form-group">
          <label>难度</label>
          <select v-model="form.difficulty">
            <option value="easy">简单</option>
            <option value="medium">中等</option>
            <option value="hard">困难</option>
          </select>
        </div>
        <div class="form-group">
          <label>题目</label>
          <textarea v-model="form.question" rows="4" placeholder="请输入题目内容"></textarea>
        </div>
        <div class="form-group">
          <label>参考答案</label>
          <textarea v-model="form.reference_answer" rows="4" placeholder="请输入参考答案"></textarea>
        </div>
        <div class="form-group">
          <label>关键要点（逗号分隔）</label>
          <input v-model="form.key_points" placeholder="要点1, 要点2, 要点3" />
        </div>
        <div class="form-group">
          <label>标签（逗号分隔）</label>
          <input v-model="form.tags" placeholder="标签1, 标签2" />
        </div>
        <div class="admin-modal-footer">
          <button class="btn-secondary" @click="showFormModal = false">取消</button>
          <button class="btn-primary" @click="submitForm" :disabled="submitting">{{ submitting ? '提交中...' : '保存' }}</button>
        </div>
      </div>
    </div>

    <!-- Batch Import Modal -->
    <div v-if="showImportModal" class="admin-modal-overlay" @click.self="showImportModal = false">
      <div class="admin-modal">
        <div class="admin-modal-header">
          <h3>批量导入题目</h3>
          <button @click="showImportModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>JSON 数据</label>
          <textarea v-model="importJson" rows="8" placeholder='粘贴题目数组 JSON，如：[{"category":"技术基础","question":"..."}]'></textarea>
        </div>
        <div class="form-group">
          <label>或上传 JSON 文件</label>
          <input type="file" accept=".json" @change="handleImportFile" />
        </div>
        <div class="admin-modal-footer">
          <button class="btn-secondary" @click="showImportModal = false">取消</button>
          <button class="btn-primary" @click="submitImport" :disabled="importing">{{ importing ? '导入中...' : '开始导入' }}</button>
        </div>
      </div>
    </div>

    <!-- Search Test Panel -->
    <div v-if="showTestPanel" class="admin-modal-overlay" @click.self="showTestPanel = false">
      <div class="admin-modal admin-modal-lg">
        <div class="admin-modal-header">
          <h3>检索测试</h3>
          <button @click="showTestPanel = false">&times;</button>
        </div>
        <div class="form-group">
          <label>查询语句</label>
          <input v-model="testForm.query" placeholder="输入自然语言查询" />
        </div>
        <div class="test-form-row">
          <div class="form-group" style="flex:1">
            <label>Top K</label>
            <input v-model.number="testForm.top_k" type="number" min="1" max="50" />
          </div>
          <div class="form-group" style="flex:1">
            <label>岗位标签（可选）</label>
            <input v-model="testForm.position_tag" placeholder="如：前端" />
          </div>
        </div>
        <div class="test-form-row">
          <div class="form-group" style="flex:1">
            <label>难度（可选）</label>
            <select v-model="testForm.difficulty">
              <option value="">不限</option>
              <option value="easy">简单</option>
              <option value="medium">中等</option>
              <option value="hard">困难</option>
            </select>
          </div>
          <div class="form-group" style="flex:1">
            <label>最低相似度 (0-1)</label>
            <input v-model.number="testForm.min_score" type="number" min="0" max="1" step="0.01" />
          </div>
        </div>
        <div style="margin-top:var(--space-3)">
          <button class="btn-primary" @click="runTestRetrieve" :disabled="testing">{{ testing ? '检索中...' : '开始检索' }}</button>
        </div>

        <!-- Test Results -->
        <div v-if="testResults.length > 0" style="margin-top:var(--space-5)">
          <h4 class="results-heading">检索结果（{{ testResults.length }} 条）</h4>
          <div v-for="(r, idx) in testResults" :key="idx" class="test-result-item">
            <div class="test-result-header">
              <span class="result-id">#{{ r.id }} — {{ r.category }}</span>
              <span class="test-score">{{ (r.similarity_score * 100).toFixed(1) }}%</span>
            </div>
            <div class="result-question">{{ truncate(r.question, 120) }}</div>
          </div>
        </div>
        <div v-if="testResults.length === 0 && tested" class="no-results">
          未找到匹配结果
        </div>

        <div class="admin-modal-footer">
          <button class="btn-secondary" @click="showTestPanel = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { questionBankApi } from '../../api/questionBank'

// ---- Constants ----
const perPage = 15
const categoryOptions = ['技术基础', '编程能力', '项目经验', '系统设计', '行为面试']
const diffMap = { easy: '简单', medium: '中等', hard: '困难' }

// ---- Stats ----
const stats = ref({ total_count: 0, vectorized_count: 0, category_count: 0, max_usage_count: 0 })
const statCards = [
  { key: 'total_count', label: '总题数', icon: '📝', color: 'var(--c-primary)', bg: 'var(--c-primary-light)' },
  { key: 'vectorized_count', label: '已向量化', icon: '🧠', color: 'var(--c-accent)', bg: 'var(--c-accent-light)' },
  { key: 'category_count', label: '题目分类数', icon: '📂', color: '#2d7a4f', bg: '#f0fdf6' },
  { key: 'max_usage_count', label: '最高使用次数', icon: '🔥', color: '#b45309', bg: '#fefce8' }
]

// ---- List / Filters ----
const list = ref([])
const total = ref(0)
const page = ref(1)
const filters = ref({ keyword: '', category: '', difficulty: '', is_enabled: '' })
let searchTimer = null

function diffBadge(d) {
  if (d === 'easy') return 'badge-green'
  if (d === 'medium') return 'badge-yellow'
  if (d === 'hard') return 'badge-red'
  return ''
}

function truncate(str, len) {
  if (!str) return '-'
  return str.length > len ? str.slice(0, len) + '...' : str
}

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadList() }, 300)
}

async function loadStats() {
  try { stats.value = await questionBankApi.stats() } catch (e) { console.error(e) }
}

async function loadList() {
  try {
    const params = {
      page: page.value,
      per_page: perPage,
      keyword: filters.value.keyword || undefined,
      category: filters.value.category || undefined,
      difficulty: filters.value.difficulty || undefined,
      is_enabled: filters.value.is_enabled === '' ? undefined : filters.value.is_enabled
    }
    const data = await questionBankApi.list(params)
    list.value = data.items
    total.value = data.total
  } catch (e) { console.error(e) }
}

// ---- Toggle / Delete ----
async function handleToggle(item) {
  try {
    const data = await questionBankApi.toggle(item.id, { is_enabled: !item.is_enabled })
    item.is_enabled = data.is_enabled
  } catch (e) { alert('操作失败: ' + (e.message || e)) }
}

async function handleDelete(item) {
  if (!confirm(`确定要删除题目 #${item.id} 吗？`)) return
  try {
    await questionBankApi.delete(item.id)
    await loadList()
    await loadStats()
  } catch (e) { alert('删除失败: ' + (e.message || e)) }
}

// ---- Reindex All ----
async function handleReindexAll() {
  if (!confirm('确定要全量重建向量索引吗？这可能需要一段时间。')) return
  try {
    await questionBankApi.reindexAll()
    alert('全量重建任务已提交')
    await loadStats()
  } catch (e) { alert('操作失败: ' + (e.message || e)) }
}

// ---- Create / Edit Modal ----
const showFormModal = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const form = ref(getEmptyForm())

function getEmptyForm() {
  return { category: '', position_tag: '', difficulty: 'medium', question: '', reference_answer: '', key_points: '', tags: '' }
}

function openCreateModal() {
  editingId.value = null
  form.value = getEmptyForm()
  showFormModal.value = true
}

function openEditModal(item) {
  editingId.value = item.id
  form.value = {
    category: item.category || '',
    position_tag: item.position_tag || '',
    difficulty: item.difficulty || 'medium',
    question: item.question || '',
    reference_answer: item.reference_answer || '',
    key_points: Array.isArray(item.key_points) ? item.key_points.join(', ') : (item.key_points || ''),
    tags: Array.isArray(item.tags) ? item.tags.join(', ') : (item.tags || '')
  }
  showFormModal.value = true
}

function buildPayload() {
  const f = form.value
  return {
    category: f.category,
    position_tag: f.position_tag || null,
    difficulty: f.difficulty,
    question: f.question,
    reference_answer: f.reference_answer || null,
    key_points: f.key_points ? f.key_points.split(',').map(s => s.trim()).filter(Boolean) : [],
    tags: f.tags ? f.tags.split(',').map(s => s.trim()).filter(Boolean) : []
  }
}

async function submitForm() {
  if (!form.value.question) return alert('请输入题目内容')
  if (!form.value.category) return alert('请选择分类')
  submitting.value = true
  try {
    const payload = buildPayload()
    if (editingId.value) {
      await questionBankApi.update(editingId.value, payload)
    } else {
      await questionBankApi.create(payload)
    }
    showFormModal.value = false
    await loadList()
    await loadStats()
  } catch (e) { alert('保存失败: ' + (e.message || e)) }
  submitting.value = false
}

// ---- Batch Import ----
const showImportModal = ref(false)
const importing = ref(false)
const importJson = ref('')

function handleImportFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => { importJson.value = reader.result }
  reader.readAsText(file)
}

async function submitImport() {
  if (!importJson.value.trim()) return alert('请输入或上传 JSON 数据')
  let parsed
  try {
    parsed = JSON.parse(importJson.value)
  } catch { return alert('JSON 格式不正确，请检查') }
  if (!Array.isArray(parsed)) return alert('JSON 必须是题目数组')
  importing.value = true
  try {
    await questionBankApi.batchImport({ questions: parsed })
    alert(`成功导入 ${parsed.length} 道题目`)
    showImportModal.value = false
    importJson.value = ''
    await loadList()
    await loadStats()
  } catch (e) { alert('导入失败: ' + (e.message || e)) }
  importing.value = false
}

// ---- Search Test Panel ----
const showTestPanel = ref(false)
const testing = ref(false)
const tested = ref(false)
const testResults = ref([])
const testForm = ref({ query: '', top_k: 5, position_tag: '', difficulty: '', min_score: 0 })

async function runTestRetrieve() {
  if (!testForm.value.query) return alert('请输入查询语句')
  testing.value = true
  tested.value = false
  testResults.value = []
  try {
    const payload = {
      query: testForm.value.query,
      top_k: testForm.value.top_k || 5,
      position_tag: testForm.value.position_tag || undefined,
      difficulty: testForm.value.difficulty || undefined,
      min_score: testForm.value.min_score || undefined
    }
    const data = await questionBankApi.testRetrieve(payload)
    testResults.value = data.results || data || []
    tested.value = true
  } catch (e) { alert('检索失败: ' + (e.message || e)) }
  testing.value = false
}

// ---- Init ----
onMounted(() => {
  loadStats()
  loadList()
})
</script>

<style scoped>
.admin-page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  letter-spacing: -0.02em;
}
.action-bar { display: flex; gap: var(--space-3); margin-bottom: var(--space-4); flex-wrap: wrap; }
.empty-row { text-align: center; color: var(--c-text-muted); padding: var(--space-8); }
.test-form-row { display: flex; gap: var(--space-3); }
.results-heading { font-size: var(--text-sm); margin-bottom: var(--space-3); color: var(--c-text); font-weight: 600; }
.result-id { font-weight: 600; font-size: var(--text-sm); }
.result-question { font-size: var(--text-sm); color: var(--c-text-secondary); margin-top: var(--space-1); }
.no-results { margin-top: var(--space-4); text-align: center; color: var(--c-text-muted); font-size: var(--text-sm); }
</style>
