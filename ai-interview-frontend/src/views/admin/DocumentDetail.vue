<template>
  <div>
    <div class="detail-header">
      <router-link to="/admin/documents" class="back-link">&larr; 返回文档列表</router-link>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>

    <template v-else-if="doc">
      <h1 class="admin-page-title">{{ doc.title }}</h1>

      <!-- 元数据卡片 -->
      <div class="card info-card">
        <div class="meta-grid">
          <div class="meta-item">
            <span class="meta-label">ID</span>
            <span class="meta-value">{{ doc.id }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">标题</span>
            <span class="meta-value bold">{{ doc.title }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">文件名</span>
            <span class="meta-value">{{ doc.filename }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">类型</span>
            <span class="meta-value">{{ doc.doc_type }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">分类</span>
            <span class="meta-value">{{ doc.category || '-' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">文件大小</span>
            <span class="meta-value">{{ formatSize(doc.file_size) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">分块数</span>
            <span class="meta-value bold">{{ doc.chunk_count ?? '-' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">状态</span>
            <span :class="['badge', doc.is_enabled ? 'badge-green' : 'badge-red']">
              {{ doc.is_enabled ? '已启用' : '已禁用' }}
            </span>
          </div>
          <div class="meta-item">
            <span class="meta-label">上传时间</span>
            <span class="meta-value">{{ formatDate(doc.created_at) }}</span>
          </div>
          <div class="meta-item full-width" v-if="doc.description">
            <span class="meta-label">简介</span>
            <span class="meta-value">{{ doc.description }}</span>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <button
          :class="doc.is_enabled ? 'btn-secondary btn-sm' : 'btn-primary btn-sm'"
          @click="handleToggle"
          :disabled="actionLoading"
        >
          {{ doc.is_enabled ? '禁用' : '启用' }}
        </button>
        <button class="btn-secondary btn-sm" @click="handleReindex" :disabled="actionLoading">
          重建索引
        </button>
        <button class="btn-danger btn-sm" @click="handleDelete" :disabled="actionLoading">
          删除
        </button>
      </div>

      <!-- 文档分块 -->
      <div class="card section-card">
        <h3 class="section-title">文档分块</h3>

        <div v-if="chunksLoading" class="loading-state">加载分块中...</div>
        <div v-else-if="chunks.length === 0" class="loading-state">暂无分块数据</div>

        <template v-else>
          <div v-for="chunk in chunks" :key="chunk.id" class="chunk-card">
            <div class="chunk-header">
              <span class="chunk-index">#{{ chunk.chunk_index }}</span>
              <span class="chunk-vectorized">
                向量化状态:
                <span :class="chunk.is_vectorized ? 'text-success' : 'text-danger'">
                  {{ chunk.is_vectorized ? '&#x2713;' : '&#x2717;' }}
                </span>
              </span>
            </div>
            <div class="chunk-content">{{ truncate(chunk.content, 200) }}</div>
          </div>

          <div class="admin-pagination" v-if="chunkTotal > chunkPerPage">
            <button class="btn-sm" :disabled="chunkPage <= 1" @click="chunkPage--; loadChunks()">上一页</button>
            <span>{{ chunkPage }} / {{ Math.ceil(chunkTotal / chunkPerPage) }}</span>
            <button class="btn-sm" :disabled="chunkPage >= Math.ceil(chunkTotal / chunkPerPage)" @click="chunkPage++; loadChunks()">下一页</button>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { knowledgeApi } from '../../api/knowledge'

const route = useRoute()
const router = useRouter()
const id = route.params.id

const doc = ref(null)
const loading = ref(true)
const actionLoading = ref(false)

const chunks = ref([])
const chunkPage = ref(1)
const chunkPerPage = 20
const chunkTotal = ref(0)
const chunksLoading = ref(true)

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function formatDate(str) {
  if (!str) return '-'
  return new Date(str).toLocaleString('zh-CN')
}

function truncate(text, max) {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '...' : text
}

async function loadDocument() {
  try {
    doc.value = await knowledgeApi.getDocument(id)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadChunks() {
  chunksLoading.value = true
  try {
    const data = await knowledgeApi.listChunks(id, { page: chunkPage.value, per_page: chunkPerPage })
    chunks.value = data.items || data
    chunkTotal.value = data.total ?? chunks.value.length
  } catch (e) {
    console.error(e)
  } finally {
    chunksLoading.value = false
  }
}

async function handleToggle() {
  actionLoading.value = true
  try {
    await knowledgeApi.toggleDocument(id, { is_enabled: !doc.value.is_enabled })
    doc.value.is_enabled = !doc.value.is_enabled
  } catch (e) {
    console.error(e)
    alert('操作失败: ' + (e.message || e))
  } finally {
    actionLoading.value = false
  }
}

async function handleReindex() {
  actionLoading.value = true
  try {
    await knowledgeApi.reindexDocument(id)
    alert('重建索引请求已发送')
    await loadDocument()
    await loadChunks()
  } catch (e) {
    console.error(e)
    alert('操作失败: ' + (e.message || e))
  } finally {
    actionLoading.value = false
  }
}

async function handleDelete() {
  if (!confirm(`确定要删除文档"${doc.value.title}"吗？此操作不可恢复。`)) return
  actionLoading.value = true
  try {
    await knowledgeApi.deleteDocument(id)
    router.push('/admin/documents')
  } catch (e) {
    console.error(e)
    alert('删除失败: ' + (e.message || e))
  } finally {
    actionLoading.value = false
  }
}

onMounted(() => {
  Promise.all([loadDocument(), loadChunks()])
})
</script>

<style scoped>
.detail-header { margin-bottom: var(--space-4); }
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
  margin-bottom: var(--space-5);
}
.loading-state { text-align: center; padding: 60px; color: var(--c-text-muted); }
.info-card { margin-bottom: var(--space-5); }
.meta-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: var(--space-4) var(--space-6); }
.meta-item { display: flex; flex-direction: column; gap: var(--space-1); }
.meta-item.full-width { grid-column: 1 / -1; }
.meta-label { font-size: var(--text-xs); color: var(--c-text-muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; font-family: var(--font-mono); }
.meta-value { font-size: var(--text-sm); word-break: break-all; }
.meta-value.bold { font-weight: 600; }
.action-bar { display: flex; gap: var(--space-2); margin-bottom: var(--space-6); }
.section-card { margin-bottom: var(--space-4); }
.section-title { font-family: var(--font-display); font-size: var(--text-lg); font-weight: 400; margin-bottom: var(--space-4); }
.text-success { color: var(--c-success); font-weight: 600; }
.text-danger { color: var(--c-danger); font-weight: 600; }
.chunk-card {
  border: 1px solid var(--c-border-light);
  border-left: 3px solid var(--c-primary);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  margin-bottom: var(--space-3);
  transition: border-color var(--duration-fast);
}
.chunk-card:hover { border-left-color: var(--c-accent); }
.chunk-header { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-2); }
.chunk-index {
  display: inline-block;
  background: var(--c-primary-light);
  color: var(--c-primary);
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
}
.chunk-vectorized { font-size: var(--text-xs); color: var(--c-text-muted); }
.chunk-content {
  font-size: var(--text-sm); line-height: 1.7; color: var(--c-text);
  font-family: var(--font-mono); white-space: pre-wrap; word-break: break-word;
}
@media (max-width: 640px) { .meta-grid { grid-template-columns: 1fr; } }
</style>
