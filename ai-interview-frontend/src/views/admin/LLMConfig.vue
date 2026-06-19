<template>
  <div>
    <div class="page-header">
      <h1 class="admin-page-title">LLM 模型配置</h1>
      <button class="btn-primary" @click="showProviderForm = !showProviderForm">
        {{ showProviderForm ? '取消' : '+ 添加提供商' }}
      </button>
    </div>

    <!-- 添加/编辑提供商表单 -->
    <div v-if="showProviderForm" class="card form-card">
      <h3 class="form-card-title">{{ editingProvider ? '编辑提供商' : '添加提供商' }}</h3>
      <div class="form-row">
        <div class="form-group">
          <label>名称</label>
          <input v-model="providerForm.name" placeholder="例如：DeepSeek、OpenAI" />
        </div>
        <div class="form-group">
          <label>Base URL</label>
          <input v-model="providerForm.base_url" placeholder="例如：https://api.deepseek.com" />
        </div>
      </div>
      <div class="form-group">
        <label>API Key {{ editingProvider ? '（留空表示不修改）' : '' }}</label>
        <input v-model="providerForm.api_key" type="password" placeholder="sk-..." />
      </div>
      <p v-if="formMsg" :class="formMsg.startsWith('&#x2705;') ? 'success-msg' : 'error-msg'">{{ formMsg }}</p>
      <div class="form-actions">
        <button class="btn-primary" @click="handleSaveProvider" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
        <button class="btn-secondary" @click="cancelProviderForm">取消</button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading card">加载中...</div>

    <!-- 提供商列表 -->
    <div v-else-if="providers.length === 0" class="empty card">
      <p>暂无 LLM 提供商配置</p>
      <p class="empty-hint">点击上方"添加提供商"按钮开始配置</p>
    </div>

    <div v-else class="provider-list">
      <div
        v-for="p in providers"
        :key="p.id"
        :class="['card', 'provider-card', { selected: selectedProviderId === p.id, disabled: !p.is_enabled }]"
        @click="selectProvider(p)"
      >
        <div class="provider-header">
          <div class="provider-info">
            <span class="provider-name">{{ p.name }}</span>
            <span :class="['badge', p.is_enabled ? 'badge-green' : 'badge-red']">
              {{ p.is_enabled ? '已启用' : '已禁用' }}
            </span>
          </div>
          <div class="provider-actions" @click.stop>
            <button class="btn-icon" title="测试连接" @click="handleTest(p)" :disabled="testing === p.id">
              {{ testing === p.id ? '...' : '&#x1F50C;' }}
            </button>
            <button class="btn-icon" title="编辑" @click="handleEditProvider(p)">&#x270F;&#xFE0F;</button>
            <button class="btn-icon" title="删除" @click="handleDeleteProvider(p)">&#x1F5D1;&#xFE0F;</button>
          </div>
        </div>
        <div class="provider-meta">
          <span>URL: {{ p.base_url }}</span>
          <span>Key: {{ p.api_key_masked }}</span>
        </div>
        <div v-if="testResult[p.id]" :class="['test-result', testResult[p.id].success ? 'test-ok' : 'test-fail']">
          {{ testResult[p.id].success
            ? `&#x2705; 连接成功 (${testResult[p.id].latency_ms}ms)`
            : `&#x274C; ${testResult[p.id].error}` }}
        </div>
        <div class="model-count">
          {{ (p.models || []).length }} 个模型
          <span v-if="(p.models || []).some(m => m.is_active)" class="active-hint">（含激活模型）</span>
        </div>
      </div>
    </div>

    <!-- 模型管理区域 -->
    <div v-if="selectedProvider" class="model-section">
      <div class="section-header">
        <h2 class="section-title">{{ selectedProvider.name }} - 模型列表</h2>
        <button class="btn-primary btn-sm" @click="showModelForm = !showModelForm">
          {{ showModelForm ? '取消' : '+ 添加模型' }}
        </button>
      </div>

      <!-- 添加/编辑模型表单 -->
      <div v-if="showModelForm" class="card form-card model-form">
        <div class="form-row">
          <div class="form-group">
            <label>模型标识</label>
            <input v-model="modelForm.model_name" placeholder="例如：deepseek-chat、gpt-4o" />
          </div>
          <div class="form-group">
            <label>显示名称</label>
            <input v-model="modelForm.display_name" placeholder="例如：DeepSeek V3、GPT-4o" />
          </div>
        </div>
        <p v-if="modelFormMsg" :class="modelFormMsg.startsWith('&#x2705;') ? 'success-msg' : 'error-msg'">{{ modelFormMsg }}</p>
        <div class="form-actions">
          <button class="btn-primary" @click="handleSaveModel" :disabled="savingModel">
            {{ savingModel ? '保存中...' : '保存' }}
          </button>
          <button class="btn-secondary" @click="cancelModelForm">取消</button>
        </div>
      </div>

      <!-- 模型列表 -->
      <div v-if="selectedProvider.models.length === 0" class="empty-models card">
        <p class="empty-hint">该提供商暂无模型</p>
      </div>

      <div v-else class="model-list">
        <div
          v-for="m in selectedProvider.models"
          :key="m.id"
          :class="['card', 'model-card', { active: m.is_active }]"
        >
          <div class="model-info">
            <div class="model-names">
              <span class="model-display">{{ m.display_name }}</span>
              <span class="model-id">{{ m.model_name }}</span>
            </div>
            <span v-if="m.is_active" class="badge badge-info">当前激活</span>
          </div>
          <div class="model-actions">
            <button
              v-if="!m.is_active"
              class="btn-primary btn-sm"
              @click="handleActivate(m)"
              :disabled="activating === m.id"
            >
              {{ activating === m.id ? '激活中...' : '激活' }}
            </button>
            <button class="btn-icon" title="编辑" @click="handleEditModel(m)">&#x270F;&#xFE0F;</button>
            <button class="btn-icon" title="删除" @click="handleDeleteModel(m)" :disabled="m.is_active">&#x1F5D1;&#xFE0F;</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  listProviders, createProvider, updateProvider, deleteProvider,
  addModel, updateModel, deleteModel, activateModel, testConfig
} from '../../api/llmConfig'

const providers = ref([])
const loading = ref(true)
const selectedProviderId = ref(null)

// 提供商表单
const showProviderForm = ref(false)
const editingProvider = ref(null)
const providerForm = ref({ name: '', base_url: '', api_key: '' })
const saving = ref(false)
const formMsg = ref('')

// 模型表单
const showModelForm = ref(false)
const editingModel = ref(null)
const modelForm = ref({ model_name: '', display_name: '' })
const savingModel = ref(false)
const modelFormMsg = ref('')

// 测试状态
const testing = ref(null)
const testResult = ref({})

// 激活状态
const activating = ref(null)

const selectedProvider = ref(null)

function selectProvider(p) {
  selectedProviderId.value = p.id
  selectedProvider.value = p
  showModelForm.value = false
  modelFormMsg.value = ''
}

// ---- 提供商操作 ----

function handleEditProvider(p) {
  editingProvider.value = p
  providerForm.value = { name: p.name, base_url: p.base_url, api_key: '' }
  showProviderForm.value = true
  formMsg.value = ''
}

function cancelProviderForm() {
  showProviderForm.value = false
  editingProvider.value = null
  providerForm.value = { name: '', base_url: '', api_key: '' }
  formMsg.value = ''
}

async function handleSaveProvider() {
  formMsg.value = ''
  const { name, base_url, api_key } = providerForm.value
  if (!name || !base_url) {
    formMsg.value = '名称和 Base URL 不能为空'
    return
  }
  if (!editingProvider.value && !api_key) {
    formMsg.value = 'API Key 不能为空'
    return
  }

  saving.value = true
  try {
    if (editingProvider.value) {
      const data = { name, base_url }
      if (api_key) data.api_key = api_key
      await updateProvider(editingProvider.value.id, data)
      formMsg.value = '✅ 更新成功'
    } else {
      await createProvider({ name, base_url, api_key })
      formMsg.value = '✅ 创建成功'
    }
    await loadProviders()
    setTimeout(() => cancelProviderForm(), 500)
  } catch (e) {
    formMsg.value = e.message
  } finally {
    saving.value = false
  }
}

async function handleDeleteProvider(p) {
  if (!confirm(`确定要删除提供商 "${p.name}" 及其所有模型吗？`)) return
  try {
    await deleteProvider(p.id)
    if (selectedProviderId.value === p.id) {
      selectedProviderId.value = null
      selectedProvider.value = null
    }
    await loadProviders()
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}

async function handleTest(p) {
  testing.value = p.id
  testResult.value[p.id] = null
  try {
    if ((p.models || []).length === 0) {
      testResult.value[p.id] = { success: false, error: '该提供商暂无模型，请先添加模型' }
      return
    }
    const model = p.models[0]
    const result = await testConfig({
      base_url: p.base_url,
      api_key: '',
      model_name: model.model_name,
      provider_id: p.id
    })
    testResult.value[p.id] = result
  } catch (e) {
    testResult.value[p.id] = { success: false, error: e.message }
  } finally {
    testing.value = null
  }
}

// ---- 模型操作 ----

function handleEditModel(m) {
  editingModel.value = m
  modelForm.value = { model_name: m.model_name, display_name: m.display_name }
  showModelForm.value = true
  modelFormMsg.value = ''
}

function cancelModelForm() {
  showModelForm.value = false
  editingModel.value = null
  modelForm.value = { model_name: '', display_name: '' }
  modelFormMsg.value = ''
}

async function handleSaveModel() {
  modelFormMsg.value = ''
  const { model_name, display_name } = modelForm.value
  if (!model_name || !display_name) {
    modelFormMsg.value = '模型标识和显示名称不能为空'
    return
  }

  savingModel.value = true
  try {
    if (editingModel.value) {
      await updateModel(editingModel.value.id, { model_name, display_name })
      modelFormMsg.value = '✅ 更新成功'
    } else {
      await addModel(selectedProviderId.value, { model_name, display_name })
      modelFormMsg.value = '✅ 添加成功'
    }
    await loadProviders()
    setTimeout(() => cancelModelForm(), 500)
  } catch (e) {
    modelFormMsg.value = e.message
  } finally {
    savingModel.value = false
  }
}

async function handleDeleteModel(m) {
  if (m.is_active) return
  if (!confirm(`确定要删除模型 "${m.display_name}" 吗？`)) return
  try {
    await deleteModel(m.id)
    await loadProviders()
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}

async function handleActivate(m) {
  activating.value = m.id
  try {
    await activateModel(m.id)
    await loadProviders()
  } catch (e) {
    alert('激活失败: ' + e.message)
  } finally {
    activating.value = null
  }
}

// ---- 数据加载 ----

async function loadProviders() {
  try {
    const data = await listProviders()
    providers.value = data || []
    if (selectedProviderId.value) {
      selectedProvider.value = providers.value.find(p => p.id === selectedProviderId.value) || null
    }
  } catch (e) {
    console.error('加载提供商列表失败:', e)
  }
}

onMounted(async () => {
  await loadProviders()
  loading.value = false
})
</script>

<style scoped>
.admin-page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  letter-spacing: -0.02em;
}
.loading, .empty { text-align: center; padding: 60px var(--space-5); }
.empty-hint { color: var(--c-text-muted); font-size: var(--text-sm); margin-top: var(--space-2); }

.form-card { margin-bottom: var(--space-4); }
.form-card-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 400;
  margin-bottom: var(--space-5);
}
.form-actions { display: flex; gap: var(--space-2); margin-top: var(--space-1); }
.success-msg { color: var(--c-success); font-size: var(--text-sm); margin-top: var(--space-1); }
.error-msg { color: var(--c-danger); font-size: var(--text-sm); margin-top: var(--space-1); }

/* 提供商列表 */
.provider-list { display: flex; flex-direction: column; gap: var(--space-3); }
.provider-card {
  cursor: pointer; transition: all var(--duration-fast) var(--ease-out);
  border: 2px solid transparent;
}
.provider-card:hover { border-color: var(--c-primary-muted); }
.provider-card.selected { border-color: var(--c-primary); background: var(--c-primary-light); }
.provider-card.disabled { opacity: 0.6; }
.provider-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2); }
.provider-info { display: flex; align-items: center; gap: var(--space-3); }
.provider-name { font-weight: 600; font-size: var(--text-base); font-family: var(--font-display); }
.provider-actions { display: flex; gap: var(--space-1); }
.btn-icon {
  background: none; border: none; padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm); cursor: pointer; font-size: 14px;
  transition: background var(--duration-fast);
}
.btn-icon:hover { background: var(--c-bg); }
.btn-icon:disabled { opacity: 0.4; cursor: not-allowed; }
.provider-meta { display: flex; gap: var(--space-5); font-size: var(--text-xs); color: var(--c-text-muted); margin-bottom: var(--space-2); font-family: var(--font-mono); }
.model-count { font-size: var(--text-xs); color: var(--c-text-muted); }
.active-hint { color: var(--c-success); font-weight: 600; }

/* 测试结果 */
.test-result { font-size: var(--text-sm); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); margin: var(--space-2) 0; }
.test-ok { background: var(--c-success-light); color: var(--c-success); }
.test-fail { background: var(--c-danger-light); color: var(--c-danger); }

/* 模型管理 */
.model-section { margin-top: var(--space-8); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4); }
.section-title { font-family: var(--font-display); font-size: var(--text-lg); font-weight: 400; }
.model-list { display: flex; flex-direction: column; gap: var(--space-2); }
.model-card { display: flex; justify-content: space-between; align-items: center; border: 2px solid transparent; transition: all var(--duration-fast); }
.model-card.active { border-color: var(--c-primary); background: var(--c-primary-light); }
.model-info { display: flex; align-items: center; gap: var(--space-3); }
.model-names { display: flex; flex-direction: column; }
.model-display { font-weight: 600; font-size: var(--text-base); }
.model-id { font-size: var(--text-xs); color: var(--c-text-muted); font-family: var(--font-mono); }
.model-actions { display: flex; align-items: center; gap: var(--space-2); }
.empty-models { text-align: center; padding: var(--space-8); }
.model-form { margin-bottom: var(--space-3); }
</style>
