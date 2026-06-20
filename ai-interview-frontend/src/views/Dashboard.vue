<template>
  <div class="container">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <h1>面试中心</h1>
      <div class="header-actions">
        <button class="btn-primary" @click="showResumePanel = !showResumePanel">
          我的简历
        </button>
        <router-link to="/resume/upload" class="btn-secondary">
          + 上传新简历
        </router-link>
      </div>
    </div>

    <!-- 简历面板（可折叠） -->
    <div v-if="showResumePanel" class="card resume-panel">
      <div class="panel-header">
        <h2 class="panel-title">我的简历</h2>
        <button class="close-panel" @click="showResumePanel = false">&times;</button>
      </div>

      <div v-if="resumesLoading" class="skeleton-list">
        <div v-for="i in 2" :key="i" class="skeleton" style="height:64px;margin-bottom:10px"></div>
      </div>
      <div v-else-if="resumes.length === 0" class="empty-state">
        <p class="empty-icon">&#x1F4C4;</p>
        <p class="empty-title">暂无简历</p>
        <p class="empty-desc">
          <router-link to="/resume/upload">上传一份简历</router-link> 开始面试
        </p>
      </div>
      <div v-else class="resume-list">
        <div v-for="r in resumes" :key="r.resume_id" class="resume-item">
          <div class="resume-info">
            <div class="resume-name">{{ r.file_name }}</div>
            <div class="resume-meta">
              <span class="resume-position">{{ r.target_position }}</span>
              <span :class="['badge', r.status === 'completed' ? 'badge-success' : r.status === 'parsing' ? 'badge-warning' : 'badge-danger']">
                {{ r.status === 'completed' ? '已解析' : r.status === 'parsing' ? '解析中...' : '解析失败' }}
              </span>
              <span class="resume-date text-muted text-xs">{{ formatDate(r.created_at) }}</span>
            </div>
          </div>
          <button
            v-if="r.status === 'completed'"
            class="btn-primary btn-sm"
            @click="openInterviewConfig(r)"
          >
            开始面试
          </button>
          <span v-else-if="r.status === 'parsing'" class="text-muted text-xs">解析中，请稍候刷新</span>
          <span v-else class="text-xs" style="color:var(--c-danger)">解析失败，请重新上传</span>
        </div>
      </div>
    </div>

    <!-- 面试配置弹窗 -->
    <div v-if="configModal" class="modal-overlay" @click.self="configModal = null">
      <div class="modal-card">
        <h3 class="modal-title">配置面试 &mdash; {{ configModal.file_name }}</h3>

        <div class="form-group">
          <label>选择岗位模板</label>
          <select v-model="configForm.template_id" @change="onTemplateChange" class="template-select">
            <option :value="null">自定义（不使用模板）</option>
            <option v-for="t in positionTemplates" :key="t.id" :value="t.id">
              {{ t.position_tag }}
            </option>
          </select>
        </div>

        <div v-if="selectedTemplate" class="template-info">
          <div v-if="selectedTemplate.core_skills?.length" class="template-tags">
            <span class="template-label">核心技能</span>
            <div class="tag-list">
              <span v-for="skill in selectedTemplate.core_skills" :key="skill" class="skill-tag">{{ skill }}</span>
            </div>
          </div>
          <div v-if="selectedTemplate.interview_focus" class="template-focus">
            <span class="template-label">面试重点</span>
            <p class="focus-text">{{ selectedTemplate.interview_focus }}</p>
          </div>
        </div>

        <div class="form-group">
          <label>目标岗位</label>
          <input v-model="configForm.target_position" placeholder="如：前端开发工程师" />
        </div>

        <div class="form-group">
          <label>面试难度</label>
          <div class="radio-group-vertical">
            <label :class="['radio-card', { active: configForm.difficulty === 'easy' }]" @click="configForm.difficulty = 'easy'">
              <span :class="['radio-dot', { checked: configForm.difficulty === 'easy' }]"></span>
              <div class="radio-card-text">
                <span class="radio-card-title">简单</span>
                <span class="radio-card-desc">基础知识点，适合入门巩固</span>
              </div>
            </label>
            <label :class="['radio-card', { active: configForm.difficulty === 'medium' }]" @click="configForm.difficulty = 'medium'">
              <span :class="['radio-dot', { checked: configForm.difficulty === 'medium' }]"></span>
              <div class="radio-card-text">
                <span class="radio-card-title">中等</span>
                <span class="radio-card-desc">技术深度与项目经验</span>
              </div>
            </label>
            <label :class="['radio-card', { active: configForm.difficulty === 'hard' }]" @click="configForm.difficulty = 'hard'">
              <span :class="['radio-dot', { checked: configForm.difficulty === 'hard' }]"></span>
              <div class="radio-card-text">
                <span class="radio-card-title">困难</span>
                <span class="radio-card-desc">系统设计与架构思维</span>
              </div>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>题目数量</label>
          <div class="radio-group">
            <label :class="['radio-option', { active: configForm.total_questions === 3 }]" @click="configForm.total_questions = 3">
              <span :class="['radio-dot-sm', { checked: configForm.total_questions === 3 }]"></span>
              <span>3 题</span>
            </label>
            <label :class="['radio-option', { active: configForm.total_questions === 5 }]" @click="configForm.total_questions = 5">
              <span :class="['radio-dot-sm', { checked: configForm.total_questions === 5 }]"></span>
              <span>5 题</span>
            </label>
            <label :class="['radio-option', { active: configForm.total_questions === 8 }]" @click="configForm.total_questions = 8">
              <span :class="['radio-dot-sm', { checked: configForm.total_questions === 8 }]"></span>
              <span>8 题</span>
            </label>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="configModal = null">取消</button>
          <button class="btn-primary" @click="handleStartInterview" :disabled="starting">
            {{ starting ? '正在生成面试题...' : '开始面试' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 面试记录 -->
    <h2 class="section-heading">面试记录</h2>

    <div v-if="interviewsLoading" class="skeleton-list">
      <div v-for="i in 3" :key="i" class="skeleton" style="height:88px;margin-bottom:12px"></div>
    </div>

    <div v-else-if="interviews.length === 0" class="empty-state card">
      <p class="empty-icon">&#x1F3AF;</p>
      <p class="empty-title">还没有面试记录</p>
      <p class="empty-desc">选择一份简历开始你的第一次 AI 模拟面试</p>
    </div>

    <div v-else class="interview-list">
      <div v-for="item in interviews" :key="item.interview_id" class="card card-hover interview-item">
        <div class="item-header">
          <span class="position">{{ item.target_position }}</span>
          <span :class="['badge', item.status === 'completed' ? 'badge-success' : 'badge-warning']">
            {{ item.status === 'completed' ? '已完成' : '进行中' }}
          </span>
        </div>
        <div class="item-meta">
          <span>难度：{{ difficultyMap[item.difficulty] || item.difficulty }}</span>
          <span>题数：{{ item.total_questions }}</span>
          <span v-if="item.overall_score">得分：{{ item.overall_score }}</span>
          <span>{{ formatDate(item.created_at) }}</span>
        </div>
        <div class="item-actions">
          <router-link v-if="item.status === 'in_progress'" :to="`/interview/${item.interview_id}`" class="btn-primary btn-sm">
            继续面试
          </router-link>
          <router-link v-else :to="`/interview/${item.interview_id}/report`" class="btn-secondary btn-sm">
            查看报告
          </router-link>
          <button class="btn-ghost btn-sm btn-delete" @click="handleDelete(item.interview_id)">
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getInterviews, deleteInterview, startInterview } from '../api/interview'
import { getResumes } from '../api/resume'
import { getPositionTemplates } from '../api/positionTemplates'
import { useToastStore } from '../stores/toast'
import { formatDate, difficultyMap } from '../utils/helpers'

const router = useRouter()
const toast = useToastStore()

// 简历
const resumes = ref([])
const resumesLoading = ref(true)
const showResumePanel = ref(false)

// 面试
const interviews = ref([])
const interviewsLoading = ref(true)

// 岗位模板
const positionTemplates = ref([])

// 面试配置弹窗
const configModal = ref(null)
const configForm = reactive({
  target_position: '',
  difficulty: 'medium',
  total_questions: 5,
  template_id: null
})
const starting = ref(false)

const selectedTemplate = computed(() => {
  if (!configForm.template_id) return null
  return positionTemplates.value.find(t => t.id === configForm.template_id) || null
})

function onTemplateChange() {
  const tpl = selectedTemplate.value
  if (tpl) {
    configForm.target_position = tpl.position_tag
  }
}

function openInterviewConfig(resume) {
  configForm.target_position = resume.target_position || 'Python后端开发工程师'
  configForm.difficulty = 'medium'
  configForm.total_questions = 5
  configForm.template_id = null
  configModal.value = resume
}

async function handleStartInterview() {
  if (!configForm.target_position.trim()) {
    toast.warning('请输入目标岗位')
    return
  }
  starting.value = true
  try {
    const data = await startInterview({
      resume_id: configModal.value.resume_id,
      target_position: configForm.target_position,
      difficulty: configForm.difficulty,
      total_questions: configForm.total_questions
    })
    configModal.value = null
    toast.success('面试已创建')
    router.push(`/interview/${data.interview_id}`)
  } catch (e) {
    toast.error('创建面试失败: ' + e.message)
  } finally {
    starting.value = false
  }
}

async function handleDelete(interviewId) {
  if (!confirm('确定要删除这条面试记录吗？删除后无法恢复。')) return
  try {
    await deleteInterview(interviewId)
    interviews.value = interviews.value.filter(i => i.interview_id !== interviewId)
    toast.success('已删除')
  } catch (e) {
    toast.error('删除失败: ' + e.message)
  }
}

onMounted(async () => {
  const [resumeData, interviewData, templateData] = await Promise.allSettled([
    getResumes(),
    getInterviews(),
    getPositionTemplates()
  ])

  if (resumeData.status === 'fulfilled') {
    resumes.value = resumeData.value || []
  }
  resumesLoading.value = false

  if (interviewData.status === 'fulfilled') {
    interviews.value = interviewData.value?.items || []
  }
  interviewsLoading.value = false

  if (templateData.status === 'fulfilled') {
    positionTemplates.value = templateData.value || []
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin: var(--space-8) 0 var(--space-6);
}
.page-header h1 {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: 400;
  letter-spacing: -0.02em;
}
.header-actions { display: flex; gap: var(--space-3); }

/* 简历面板 */
.resume-panel { margin-bottom: var(--space-2); }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
}
.close-panel {
  background: none; border: 1.5px solid transparent; font-size: 18px;
  color: var(--c-text-muted); cursor: pointer; padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: all var(--duration-fast);
}
.close-panel:hover { color: var(--c-text); background: var(--c-text); color: var(--c-surface); }
.panel-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 400;
  margin: 0;
}
.section-heading {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  margin: var(--space-10) 0 var(--space-5);
  color: var(--c-text);
  letter-spacing: -0.01em;
  border-bottom: 2px solid var(--c-border);
  padding-bottom: var(--space-3);
}
.modal-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 400;
  margin-bottom: var(--space-6);
  color: var(--c-text);
}
.modal-actions {
  display: flex; justify-content: flex-end; gap: var(--space-3);
  margin-top: var(--space-8); padding-top: var(--space-5);
  border-top: 2px solid var(--c-border-light);
}
.btn-delete {
  color: var(--c-text-muted); background: transparent; border: 1.5px solid transparent;
}
.btn-delete:hover { color: var(--c-danger); background: var(--c-danger-light); border-color: var(--c-danger); }
.resume-list { display: flex; flex-direction: column; gap: var(--space-3); }

/* 岗位模板选择器 */
.template-select {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  background: var(--c-surface);
  color: var(--c-text);
  cursor: pointer;
  transition: border-color var(--duration-fast);
  appearance: auto;
}
.template-select:focus {
  outline: none;
  border-color: var(--c-primary);
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}

.template-info {
  background: var(--c-primary-light);
  border: 1px solid var(--c-primary);
  border-radius: var(--radius-sm);
  padding: var(--space-4);
  margin-bottom: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.template-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--c-primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  display: block;
  margin-bottom: var(--space-1);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.skill-tag {
  display: inline-block;
  padding: 2px 10px;
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  background: var(--c-surface);
  color: var(--c-primary);
  border: 1px solid var(--c-primary);
  border-radius: 999px;
}

.focus-text {
  font-size: var(--text-sm);
  color: var(--c-text-secondary);
  margin: 0;
  line-height: 1.6;
}
.resume-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--space-4) var(--space-5);
  background: var(--c-surface);
  border-radius: var(--radius-sm);
  border: 1px solid var(--c-border);
  transition: all var(--duration-fast);
}
.resume-item:hover { border-color: var(--c-border); box-shadow: var(--shadow-sm); }
.resume-name { font-weight: 600; font-size: var(--text-base); color: var(--c-text); }
.resume-meta { display: flex; gap: var(--space-4); font-size: var(--text-xs); margin-top: var(--space-1); font-family: var(--font-mono); }
.resume-position { color: var(--c-primary); font-weight: 500; }

/* 面试配置 - Radio 选择 */
.radio-group-vertical { display: flex; flex-direction: column; gap: var(--space-2); }
.radio-card {
  display: flex; align-items: center; gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--duration-fast);
  background: var(--c-surface);
}
.radio-card:hover {
  border-color: var(--c-border);
  box-shadow: var(--shadow-xs);
}
.radio-card.active {
  border-color: var(--c-primary);
  background: var(--c-primary-light);
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
.radio-card-text { display: flex; flex-direction: column; gap: 2px; }
.radio-card-title { font-size: var(--text-base); font-weight: 600; color: var(--c-text); }
.radio-card.active .radio-card-title { color: var(--c-primary); }
.radio-card-desc { font-size: var(--text-xs); color: var(--c-text-muted); font-family: var(--font-mono); letter-spacing: 0.02em; }
.radio-card.active .radio-card-desc { color: var(--c-primary-hover); }

.radio-dot {
  width: 20px; height: 20px; border-radius: 50%;
  border: 1px solid var(--c-border); flex-shrink: 0;
  position: relative; transition: all var(--duration-fast);
  background: var(--c-surface);
}
.radio-dot.checked { border-color: var(--c-primary); }
.radio-dot.checked::after {
  content: ''; position: absolute;
  top: 3px; left: 3px; width: 10px; height: 10px;
  border-radius: 50%; background: var(--c-primary);
}

.radio-group { display: flex; gap: var(--space-2); }
.radio-option {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--c-border); border-radius: var(--radius-sm);
  text-align: center; font-size: var(--text-base); font-weight: 500;
  cursor: pointer; transition: all var(--duration-fast);
  color: var(--c-text-secondary); background: var(--c-surface);
}
.radio-option:hover { border-color: var(--c-border); color: var(--c-text); }
.radio-option.active {
  background: var(--c-primary-light); border-color: var(--c-primary); color: var(--c-primary);
  font-weight: 600; box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}

.radio-dot-sm {
  width: 16px; height: 16px; border-radius: 50%;
  border: 1px solid var(--c-border); flex-shrink: 0;
  position: relative; transition: all var(--duration-fast);
  background: var(--c-surface);
}
.radio-dot-sm.checked { border-color: var(--c-primary); }
.radio-dot-sm.checked::after {
  content: ''; position: absolute;
  top: 2px; left: 2px; width: 8px; height: 8px;
  border-radius: 50%; background: var(--c-primary);
}

/* 面试记录 */
.interview-list { display: flex; flex-direction: column; gap: var(--space-3); }
.interview-item { display: flex; flex-direction: column; gap: var(--space-3); }
.item-header { display: flex; justify-content: space-between; align-items: center; }
.position {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: var(--text-lg);
}
.item-meta { display: flex; gap: var(--space-5); font-size: var(--text-xs); color: var(--c-text-secondary); flex-wrap: wrap; font-family: var(--font-mono); letter-spacing: 0.02em; }
.item-actions { display: flex; gap: var(--space-2); }

/* 骨架屏 */
.skeleton-list { margin-bottom: var(--space-3); }

/* 响应式 */
@media (max-width: 640px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: var(--space-3); }
  .header-actions { width: 100%; }
  .header-actions > * { flex: 1; text-align: center; }
  .resume-item { flex-direction: column; align-items: flex-start; gap: var(--space-2); }
  .item-meta { flex-wrap: wrap; gap: var(--space-2); }
}
</style>
