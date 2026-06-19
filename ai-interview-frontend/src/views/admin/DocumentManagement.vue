<template>
  <div>
    <div class="page-header">
      <h1 class="admin-page-title">&#x1F4C4; 文档管理</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="showTestModal = true">检索测试</button>
        <button class="btn-primary" @click="showUploadModal = true">上传文档</button>
      </div>
    </div>

    <div class="filter-bar">
      <input v-model="keyword" placeholder="搜索标题..." @input="debouncedSearch" />
      <select v-model="category" @change="page = 1; loadDocuments()">
        <option value="">全部分类</option>
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
      <select v-model="status" @change="page = 1; loadDocuments()">
        <option value="">全部状态</option>
        <option value="1">已启用</option>
        <option value="0">已禁用</option>
      </select>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>标题</th>
            <th>类型</th>
            <th>分类</th>
            <th>大小</th>
            <th>分块数</th>
            <th>状态</th>
            <th>上传时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="9" class="empty-row">加载中...</td>
          </tr>
          <tr v-else-if="!documents.length">
            <td colspan="9" class="empty-row">暂无文档</td>
          </tr>
          <tr v-for="doc in documents" :key="doc.id">
            <td>{{ doc.id }}</td>
            <td>{{ doc.title }}</td>
            <td>{{ doc.doc_type }}</td>
            <td>{{ doc.category || '-' }}</td>
            <td>{{ formatSize(doc.file_size) }}</td>
            <td>{{ doc.chunk_count ?? '-' }}</td>
            <td>
              <span :class="['badge', doc.is_enabled ? 'badge-green' : 'badge-red']">
                {{ doc.is_enabled ? '启用' : '禁用' }}
              </span>
            </td>
            <td>{{ formatDate(doc.created_at) }}</td>
            <td class="action-cell">
              <router-link :to="`/admin/documents/${doc.id}`" class="btn-primary btn-sm" style="text-decoration:none;color:white">详情</router-link>
              <button :class="doc.is_enabled ? 'btn-danger btn-sm' : 'btn-primary btn-sm'" @click="toggleDoc(doc)">
                {{ doc.is_enabled ? '禁用' : '启用' }}
              </button>
              <button class="btn-secondary btn-sm" :disabled="doc._reindexing" @click="reindexDoc(doc)">
                {{ doc._reindexing ? '处理中' : '重建索引' }}
              </button>
              <button class="btn-danger btn-sm" @click="deleteDoc(doc)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="admin-pagination" v-if="total > perPage">
        <button class="btn-sm" :disabled="page <= 1" @click="page--; loadDocuments()">上一页</button>
        <span>{{ page }} / {{ Math.ceil(total / perPage) }}</span>
        <button class="btn-sm" :disabled="page >= Math.ceil(total / perPage)" @click="page++; loadDocuments()">下一页</button>
      </div>
    </div>

    <!-- Upload Modal -->
    <div v-if="showUploadModal" class="admin-modal-overlay" @click.self="closeUploadModal">
      <div class="admin-modal">
        <div class="admin-modal-header">
          <h3>上传文档</h3>
          <button class="btn-sm" @click="closeUploadModal">&times;</button>
        </div>
        <form @submit.prevent="uploadDocument">
          <div class="form-group">
            <label>文件</label>
            <input type="file" ref="fileInput" accept=".pdf,.docx,.txt,.md" required />
          </div>
          <div class="form-group">
            <label>标题</label>
            <input v-model="uploadForm.title" placeholder="文档标题（可选，默认使用文件名）" />
          </div>
          <div class="form-group">
            <label>分类</label>
            <input v-model="uploadForm.category" placeholder="如：公司制度、技术文档" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="uploadForm.description" placeholder="文档描述（可选）" rows="3"></textarea>
          </div>
          <div class="admin-modal-footer">
            <button type="button" class="btn-secondary" @click="closeUploadModal">取消</button>
            <button type="submit" class="btn-primary" :disabled="uploading">{{ uploading ? '上传中...' : '上传' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Search Test Modal -->
    <div v-if="showTestModal" class="admin-modal-overlay" @click.self="closeTestModal">
      <div class="admin-modal">
        <div class="admin-modal-header">
          <h3>检索测试</h3>
          <button class="btn-sm" @click="closeTestModal">&times;</button>
        </div>
        <form @submit.prevent="testRetrieve">
          <div class="form-group">
            <label>查询内容</label>
            <input v-model="testForm.query" placeholder="输入检索内容..." required />
          </div>
          <div class="form-row">
            <div class="form-group" style="flex:1">
              <label>Top K</label>
              <input type="number" v-model.number="testForm.top_k" min="1" max="20" />
            </div>
            <div class="form-group" style="flex:1">
              <label>分类过滤</label>
              <input v-model="testForm.category" placeholder="可选" />
            </div>
          </div>
          <div class="admin-modal-footer">
            <button type="button" class="btn-secondary" @click="closeTestModal">关闭</button>
            <button type="submit" class="btn-primary" :disabled="testing">{{ testing ? '检索中...' : '检索' }}</button>
          </div>
        </form>
        <div v-if="testResults.length" class="test-results">
          <h4 class="results-heading">检索结果</h4>
          <div v-for="(r, i) in testResults" :key="i" class="test-result-item">
            <div class="test-result-header">
              <span class="test-score">相似度: {{ r.similarity_score?.toFixed(4) ?? '-' }}</span>
              <span class="test-doc-title">{{ r.document_title || '-' }}</span>
            </div>
            <p class="test-chunk-content">{{ r.chunk_content || '' }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { knowledgeApi } from '../../api/knowledge'

const documents = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 15
const loading = ref(false)
const keyword = ref('')
const category = ref('')
const status = ref('')
const categories = ref([])
let searchTimer = null

// Upload
const showUploadModal = ref(false)
const uploading = ref(false)
const fileInput = ref(null)
const uploadForm = ref({ title: '', category: '', description: '' })

// Test retrieve
const showTestModal = ref(false)
const testing = ref(false)
const testForm = ref({ query: '', top_k: 5, category: '' })
const testResults = ref([])

function formatSize(bytes) {
  if (bytes == null) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function formatDate(str) {
  if (!str) return ''
  return new Date(str).toLocaleString('zh-CN')
}

async function loadDocuments() {
  loading.value = true
  try {
    const params = { page: page.value, per_page: perPage }
    if (keyword.value) params.keyword = keyword.value
    if (category.value) params.category = category.value
    if (status.value !== '') params.is_enabled = status.value
    const data = await knowledgeApi.listDocuments(params)
    documents.value = data.items || []
    total.value = data.total || 0
    if (data.categories) categories.value = data.categories
  } catch (e) { console.error(e) }
  loading.value = false
}

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadDocuments() }, 300)
}

async function toggleDoc(doc) {
  try {
    const data = await knowledgeApi.toggleDocument(doc.id, { is_enabled: !doc.is_enabled })
    doc.is_enabled = data.is_enabled
  } catch (e) { console.error(e); alert('操作失败') }
}

async function reindexDoc(doc) {
  if (!confirm('确定要重建该文档的索引吗？')) return
  doc._reindexing = true
  try {
    await knowledgeApi.reindexDocument(doc.id)
    alert('索引重建已提交')
    await loadDocuments()
  } catch (e) { console.error(e); alert('重建索引失败') }
  doc._reindexing = false
}

async function deleteDoc(doc) {
  if (!confirm(`确定要删除文档「${doc.title}」吗？此操作不可撤销。`)) return
  try {
    await knowledgeApi.deleteDocument(doc.id)
    await loadDocuments()
  } catch (e) { console.error(e); alert('删除失败') }
}

function closeUploadModal() {
  showUploadModal.value = false
  uploadForm.value = { title: '', category: '', description: '' }
}

async function uploadDocument() {
  const files = fileInput.value?.files
  if (!files || !files.length) return alert('请选择文件')
  uploading.value = true
  const fd = new FormData()
  fd.append('file', files[0])
  if (uploadForm.value.title) fd.append('title', uploadForm.value.title)
  if (uploadForm.value.category) fd.append('category', uploadForm.value.category)
  if (uploadForm.value.description) fd.append('description', uploadForm.value.description)
  try {
    await knowledgeApi.uploadDocument(fd)
    closeUploadModal()
    await loadDocuments()
  } catch (e) { console.error(e); alert('上传失败') }
  uploading.value = false
}

function closeTestModal() {
  showTestModal.value = false
  testResults.value = []
  testForm.value = { query: '', top_k: 5, category: '' }
}

async function testRetrieve() {
  testing.value = true
  testResults.value = []
  try {
    const body = { query: testForm.value.query, top_k: testForm.value.top_k }
    if (testForm.value.category) body.category = testForm.value.category
    const data = await knowledgeApi.testRetrieve(body)
    testResults.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) { console.error(e); alert('检索失败') }
  testing.value = false
}

onMounted(loadDocuments)
</script>

<style scoped>
.admin-page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  letter-spacing: -0.02em;
}
.empty-row { text-align: center; color: var(--c-text-muted); padding: var(--space-8); }
.results-heading { font-size: var(--text-sm); margin-bottom: var(--space-3); color: var(--c-text); font-weight: 600; }
</style>
