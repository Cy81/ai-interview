<template>
  <div>
    <div class="page-header">
      <h1 class="admin-page-title">&#x1F4CB; 岗位模板</h1>
      <button class="btn-primary" @click="openCreateModal">+ 新增模板</button>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>岗位标签</th>
            <th>标题</th>
            <th>分类</th>
            <th>级别</th>
            <th>核心技能</th>
            <th>推荐难度</th>
            <th>推荐题数</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in templates" :key="t.id">
            <td>{{ t.id }}</td>
            <td>{{ t.position_tag }}</td>
            <td>{{ t.title }}</td>
            <td>{{ t.category || '-' }}</td>
            <td>{{ levelMap[t.level] || t.level || '-' }}</td>
            <td>
              <span v-for="skill in parseSkills(t.core_skills)" :key="skill" class="skill-tag">{{ skill }}</span>
              <span v-if="!parseSkills(t.core_skills).length" class="empty-dash">-</span>
            </td>
            <td>
              <span :class="['badge', difficultyBadge(t.recommended_difficulty)]">
                {{ difficultyMap[t.recommended_difficulty] || t.recommended_difficulty || '-' }}
              </span>
            </td>
            <td>{{ t.recommended_questions ?? '-' }}</td>
            <td>
              <span :class="['badge', t.is_enabled ? 'badge-green' : 'badge-red']">
                {{ t.is_enabled ? '启用' : '禁用' }}
              </span>
            </td>
            <td class="action-cell">
              <button class="btn-primary btn-sm" @click="openEditModal(t)">编辑</button>
              <button
                :class="t.is_enabled ? 'btn-danger btn-sm' : 'btn-secondary btn-sm'"
                @click="handleToggle(t)"
              >
                {{ t.is_enabled ? '禁用' : '启用' }}
              </button>
              <button class="btn-danger btn-sm" @click="handleDelete(t)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="admin-pagination" v-if="total > perPage">
        <button class="btn-sm" :disabled="page <= 1" @click="page--; loadTemplates()">上一页</button>
        <span>{{ page }} / {{ Math.ceil(total / perPage) }}</span>
        <button class="btn-sm" :disabled="page >= Math.ceil(total / perPage)" @click="page++; loadTemplates()">下一页</button>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <div v-if="showModal" class="admin-modal-overlay" @click.self="closeModal">
      <div class="admin-modal admin-modal-lg">
        <div class="admin-modal-header">
          <h3>{{ editing ? '编辑模板' : '新增模板' }}</h3>
          <button @click="closeModal">&times;</button>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>岗位标签 <span class="required">*</span></label>
            <input v-model="form.position_tag" placeholder="例如：后端工程师" />
          </div>
          <div class="form-group">
            <label>标题 <span class="required">*</span></label>
            <input v-model="form.title" placeholder="例如：Java 高级后端工程师" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>分类</label>
            <input v-model="form.category" placeholder="例如：后端开发" />
          </div>
          <div class="form-group">
            <label>级别</label>
            <select v-model="form.level">
              <option value="">请选择</option>
              <option value="junior">初级</option>
              <option value="mid">中级</option>
              <option value="senior">高级</option>
              <option value="lead">专家</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>描述</label>
          <textarea v-model="form.description" rows="3" placeholder="岗位描述..."></textarea>
        </div>

        <div class="form-group">
          <label>核心技能</label>
          <input v-model="form.core_skills" placeholder="逗号分隔，例如：Java,Spring Boot,MySQL" />
        </div>

        <div class="form-group">
          <label>面试重点</label>
          <textarea v-model="form.interview_focus" rows="3" placeholder="面试考察重点方向..."></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>推荐难度</label>
            <select v-model="form.recommended_difficulty">
              <option value="">请选择</option>
              <option value="easy">简单</option>
              <option value="medium">中等</option>
              <option value="hard">困难</option>
            </select>
          </div>
          <div class="form-group">
            <label>推荐题数</label>
            <input v-model.number="form.recommended_questions" type="number" min="1" placeholder="默认 5" />
          </div>
        </div>

        <div class="form-group">
          <label>评价标准</label>
          <textarea v-model="form.key_evaluation_criteria" rows="3" placeholder="关键评价标准..."></textarea>
        </div>

        <p v-if="formMsg" :class="formMsg.startsWith('&#x2705;') ? 'success-msg' : 'error-msg'">{{ formMsg }}</p>

        <div class="admin-modal-footer">
          <button class="btn-primary" @click="handleSubmit" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button class="btn-secondary" @click="closeModal">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { positionTemplateApi } from '../../api/positionTemplate'

const templates = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 15

const showModal = ref(false)
const editing = ref(null)
const saving = ref(false)
const formMsg = ref('')

const levelMap = { junior: '初级', mid: '中级', senior: '高级', lead: '专家' }
const difficultyMap = { easy: '简单', medium: '中等', hard: '困难' }

const emptyForm = {
  position_tag: '',
  title: '',
  category: '',
  level: '',
  description: '',
  core_skills: '',
  interview_focus: '',
  recommended_difficulty: '',
  recommended_questions: 5,
  key_evaluation_criteria: ''
}

const form = ref({ ...emptyForm })

function parseSkills(val) {
  if (!val) return []
  if (Array.isArray(val)) return val.filter(Boolean)
  return val.split(',').map(s => s.trim()).filter(Boolean)
}

function difficultyBadge(d) {
  if (d === 'easy') return 'badge-green'
  if (d === 'medium') return 'badge-yellow'
  if (d === 'hard') return 'badge-red'
  return ''
}

async function loadTemplates() {
  try {
    const data = await positionTemplateApi.list({ page: page.value, per_page: perPage })
    templates.value = data.items
    total.value = data.total
  } catch (e) { console.error(e) }
}

function openCreateModal() {
  editing.value = null
  form.value = { ...emptyForm }
  formMsg.value = ''
  showModal.value = true
}

function openEditModal(t) {
  editing.value = t
  form.value = {
    position_tag: t.position_tag || '',
    title: t.title || '',
    category: t.category || '',
    level: t.level || '',
    description: t.description || '',
    core_skills: Array.isArray(t.core_skills) ? t.core_skills.join(',') : (t.core_skills || ''),
    interview_focus: t.interview_focus || '',
    recommended_difficulty: t.recommended_difficulty || '',
    recommended_questions: t.recommended_questions ?? 5,
    key_evaluation_criteria: t.key_evaluation_criteria || ''
  }
  formMsg.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editing.value = null
  formMsg.value = ''
}

async function handleSubmit() {
  formMsg.value = ''
  if (!form.value.position_tag || !form.value.title) {
    formMsg.value = '岗位标签和标题不能为空'
    return
  }

  saving.value = true
  try {
    const payload = { ...form.value }
    if (!payload.recommended_questions) payload.recommended_questions = 5

    if (editing.value) {
      await positionTemplateApi.update(editing.value.id, payload)
      formMsg.value = '✅ 更新成功'
    } else {
      await positionTemplateApi.create(payload)
      formMsg.value = '✅ 创建成功'
    }
    await loadTemplates()
    setTimeout(() => closeModal(), 500)
  } catch (e) {
    formMsg.value = e.message || '操作失败'
  } finally {
    saving.value = false
  }
}

async function handleToggle(t) {
  try {
    const data = await positionTemplateApi.toggle(t.id, { is_enabled: !t.is_enabled })
    t.is_enabled = data.is_enabled ?? !t.is_enabled
  } catch (e) { console.error(e) }
}

async function handleDelete(t) {
  if (!confirm(`确定要删除模板"${t.title}"吗？`)) return
  try {
    await positionTemplateApi.delete(t.id)
    await loadTemplates()
  } catch (e) { alert('删除失败: ' + e.message) }
}

onMounted(loadTemplates)
</script>

<style scoped>
.admin-page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  letter-spacing: -0.02em;
}
.skill-tag {
  display: inline-block;
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--c-primary-light);
  color: var(--c-primary);
  margin: 1px 2px;
  white-space: nowrap;
  font-weight: 500;
  font-family: var(--font-mono);
}
.empty-dash { color: var(--c-text-muted); }
.required { color: var(--c-danger); }
.success-msg { color: var(--c-success); font-size: var(--text-sm); margin-top: var(--space-1); }
.error-msg { color: var(--c-danger); font-size: var(--text-sm); margin-top: var(--space-1); }
</style>
