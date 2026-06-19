<template>
  <div class="interview-page">
    <!-- 面试准备动画 -->
    <div v-if="preparing" class="prepare-overlay">
      <div class="prepare-card">
        <div class="ai-face-large">
          <svg viewBox="0 0 80 80" width="80" height="80">
            <circle cx="40" cy="40" r="38" fill="white" stroke="var(--c-primary)" stroke-width="2"/>
            <ellipse cx="28" cy="36" rx="5" ry="6" fill="#1a1a1a">
              <animate attributeName="ry" values="6;1;6" dur="2.5s" repeatCount="indefinite"/>
            </ellipse>
            <ellipse cx="52" cy="36" rx="5" ry="6" fill="#1a1a1a">
              <animate attributeName="ry" values="6;1;6" dur="2.5s" repeatCount="indefinite"/>
            </ellipse>
            <path d="M30 52 Q40 60 50 52" stroke="#1a1a1a" stroke-width="2" fill="none" stroke-linecap="round"/>
          </svg>
        </div>
        <h2 class="prepare-title">面试即将开始</h2>
        <p class="prepare-tip">{{ prepareTip }}</p>
        <div class="prepare-progress">
          <div class="prepare-bar" :style="{ width: preparePercent + '%' }"></div>
        </div>
        <p class="prepare-subtitle">AI 正在为你准备面试题目...</p>
      </div>
    </div>

    <!-- 顶部状态栏 -->
    <div class="interview-header" v-if="!preparing">
      <div class="header-left">
        <span class="header-ai-mark">AI</span>
        <span class="header-title">面试官</span>
      </div>
      <span class="progress">第 {{ currentIndex + 1 }} / {{ totalQuestions }} 题</span>
      <router-link to="/dashboard" class="btn-ghost btn-sm exit-btn">退出</router-link>
    </div>

    <!-- 聊天区域 -->
    <div class="chat-area" ref="chatArea" v-if="!preparing">
      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
        <!-- AI 头像 -->
        <div v-if="msg.role === 'interviewer'" class="avatar-col">
          <div class="ai-avatar-wrap">
            <svg viewBox="0 0 40 40" width="36" height="36" class="ai-avatar">
              <circle cx="20" cy="20" r="19" fill="white" stroke="var(--c-border)" stroke-width="1"/>
              <ellipse cx="14" cy="17" rx="2.5" ry="3" fill="#1a1a1a"/>
              <ellipse cx="26" cy="17" rx="2.5" ry="3" fill="#1a1a1a"/>
            </svg>
          </div>
        </div>
        <div class="bubble">
          <div class="bubble-content" v-html="renderContent(msg.content)"></div>
          <div v-if="msg.score" class="bubble-score">{{ msg.score }}/10</div>
        </div>
        <!-- 用户头像 -->
        <div v-if="msg.role === 'candidate'" class="avatar-col">
          <img v-if="userAvatar && !avatarError" :src="userAvatar" class="user-avatar" alt="me" @error="avatarError = true" />
          <div v-else class="user-avatar-placeholder">{{ userInitial }}</div>
        </div>
      </div>

      <!-- 流式输出 -->
      <div v-if="streamingText" class="message interviewer">
        <div class="avatar-col">
          <div class="ai-avatar-wrap thinking">
            <svg viewBox="0 0 40 40" width="36" height="36" class="ai-avatar">
              <circle cx="20" cy="20" r="19" fill="white" stroke="var(--c-primary)" stroke-width="1.5"/>
              <ellipse cx="14" cy="17" rx="2.5" ry="3" fill="#1a1a1a">
                <animate attributeName="ry" values="3;1;3" dur="1.5s" repeatCount="indefinite"/>
              </ellipse>
              <ellipse cx="26" cy="17" rx="2.5" ry="3" fill="#1a1a1a">
                <animate attributeName="ry" values="3;1;3" dur="1.5s" repeatCount="indefinite"/>
              </ellipse>
            </svg>
          </div>
        </div>
        <div class="bubble">
          <div class="bubble-content streaming-content" v-html="renderContent(streamingText)"></div>
          <span class="cursor-blink">&#x2588;</span>
        </div>
      </div>

      <!-- AI 思考中 -->
      <div v-if="thinking && !streamingText" class="message interviewer">
        <div class="avatar-col">
          <div class="ai-avatar-wrap thinking">
            <svg viewBox="0 0 40 40" width="36" height="36" class="ai-avatar">
              <circle cx="20" cy="20" r="19" fill="white" stroke="var(--c-primary)" stroke-width="1.5"/>
              <ellipse cx="14" cy="17" rx="2.5" ry="3" fill="#1a1a1a">
                <animate attributeName="ry" values="3;1;3" dur="1s" repeatCount="indefinite"/>
              </ellipse>
              <ellipse cx="26" cy="17" rx="2.5" ry="3" fill="#1a1a1a">
                <animate attributeName="ry" values="3;1;3" dur="1s" repeatCount="indefinite"/>
              </ellipse>
            </svg>
          </div>
        </div>
        <div class="bubble thinking-bubble">
          <span class="dot-animation">AI 思考中<span class="dots"></span></span>
        </div>
      </div>

      <!-- 网络错误恢复 -->
      <div v-if="streamError" class="message interviewer">
        <div class="avatar-col">
          <div class="ai-avatar-wrap">
            <svg viewBox="0 0 40 40" width="36" height="36" class="ai-avatar">
              <circle cx="20" cy="20" r="19" fill="white" stroke="var(--c-border)" stroke-width="1"/>
              <ellipse cx="14" cy="17" rx="2.5" ry="3" fill="#1a1a1a"/>
              <ellipse cx="26" cy="17" rx="2.5" ry="3" fill="#1a1a1a"/>
            </svg>
          </div>
        </div>
        <div class="bubble error-bubble">
          <p>网络异常，上次回答未成功</p>
          <button class="btn-primary btn-sm" @click="retryLastAnswer" style="margin-top:10px">重新发送</button>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area" v-if="!preparing && !finished">
      <textarea
        v-model="answer"
        placeholder="输入你的回答... (Enter 发送, Shift+Enter 换行)"
        @keydown.enter.exact.prevent="handleSubmit"
        @keydown.shift.enter="handleShiftEnter"
        :disabled="thinking"
        rows="3"
      ></textarea>
      <button class="btn-primary send-btn" @click="handleSubmit" :disabled="!answer.trim() || thinking">
        {{ thinking ? '评估中...' : '发送' }}
      </button>
    </div>

    <!-- 面试结束 -->
    <div class="input-area finished" v-if="!preparing && finished">
      <p class="finished-title">面试结束</p>
      <router-link :to="`/interview/${interviewId}/report`" class="btn-primary report-btn">
        查看评估报告
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { submitAnswerStream, getMessages } from '../api/interview'
import { escapeHtml } from '../utils/helpers'

const route = useRoute()
const authStore = useAuthStore()
const interviewId = route.params.id

const messages = ref([])
const answer = ref('')
const thinking = ref(false)
const finished = ref(false)
const currentIndex = ref(0)
const totalQuestions = ref(5)
const chatArea = ref(null)
const streamingText = ref('')
const streamError = ref(false)
const lastAnswer = ref('')

// 准备动画
const preparing = ref(true)
const preparePercent = ref(0)
const prepareTips = [
  '请做好准备，保持冷静自信',
  '回答时尽量结合项目经验',
  '注意条理清晰，分点作答',
  '面试官会根据你的简历提问'
]
const prepareTip = ref(prepareTips[0])

// 用户头像
const userAvatar = computed(() => authStore.userAvatar || '')
const avatarError = ref(false)
const userInitial = computed(() => {
  const name = authStore.userName || ''
  return name.charAt(0).toUpperCase() || 'U'
})

function renderContent(text) {
  if (!text) return ''
  let cleaned = text
    .replace(/```json\s*\{[\s\S]*?\}\s*```/g, '')
    .replace(/\{[^{}]*"score"\s*:\s*[\d.]+[^{}]*\}/g, '')
    .trim()
  return escapeHtml(cleaned).replace(/\n/g, '<br>')
}

function scrollToBottom() {
  nextTick(() => {
    if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight
  })
}

function handleShiftEnter(e) {
  const textarea = e.target
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  answer.value = answer.value.substring(0, start) + '\n' + answer.value.substring(end)
  nextTick(() => {
    textarea.selectionStart = textarea.selectionEnd = start + 1
  })
}

onMounted(async () => {
  let tipIdx = 0
  const tipTimer = setInterval(() => {
    tipIdx = (tipIdx + 1) % prepareTips.length
    prepareTip.value = prepareTips[tipIdx]
  }, 1500)

  const barTimer = setInterval(() => {
    if (preparePercent.value < 90) preparePercent.value += 2
  }, 100)

  try {
    const data = await getMessages(interviewId)
    const msgList = Array.isArray(data) ? data : (data.items || data)
    messages.value = msgList.map(m => ({
      role: m.role, content: m.content, score: m.score, feedback: m.feedback
    }))
    const indices = msgList.map(m => m.question_index).filter(i => i != null)
    if (indices.length) currentIndex.value = Math.max(...indices)
  } catch (e) {
    console.error('加载消息失败:', e)
  }

  preparePercent.value = 100
  clearInterval(barTimer)
  clearInterval(tipTimer)
  setTimeout(() => { preparing.value = false }, 600)
  nextTick(scrollToBottom)
})

async function handleSubmit() {
  if (!answer.value.trim() || thinking.value) return
  const myAnswer = answer.value.trim()
  answer.value = ''
  lastAnswer.value = myAnswer
  streamError.value = false
  messages.value.push({ role: 'candidate', content: myAnswer })
  scrollToBottom()
  thinking.value = true
  streamingText.value = ''
  let rawStreamText = ''

  try {
    await submitAnswerStream(interviewId, myAnswer,
      (chunk) => {
        rawStreamText += chunk
        let display = rawStreamText
          .replace(/```json\s*\{[\s\S]*?\}\s*```/g, '')
          .replace(/\{[^{}]*"score"\s*:\s*[\d.]+[^{}]*\}/g, '')
        display = display.replace(/```json[\s\S]*$/g, '')
        display = display.replace(/\{[^}]*$/g, function(match) {
          return /["']?score/.test(match) || /^\{\s*$/.test(match) ? '' : match
        })
        streamingText.value = display.trim()
        scrollToBottom()
      },
      (data) => {
        if (rawStreamText.trim()) {
          let displayText = rawStreamText
            .replace(/```json\s*\{[\s\S]*?\}\s*```/g, '')
            .replace(/\{[^{}]*"score"\s*:\s*[\d.]+[^{}]*\}/g, '')
            .trim()
          if (displayText) {
            messages.value.push({ role: 'interviewer', content: displayText, score: data.score })
          }
        }
        streamingText.value = ''
        rawStreamText = ''
        const lastCandidate = [...messages.value].reverse().find(m => m.role === 'candidate')
        if (lastCandidate) lastCandidate.score = data.score

        if (data.is_finished) {
          finished.value = true
        } else if (data.next_question) {
          currentIndex.value = data.question_index + 1
          messages.value.push({ role: 'interviewer', content: data.next_question })
        }
        scrollToBottom()
      }
    )
  } catch (e) {
    streamingText.value = ''
    streamError.value = true
    scrollToBottom()
  } finally {
    thinking.value = false
  }
}

async function retryLastAnswer() {
  if (!lastAnswer.value) return
  streamError.value = false
  answer.value = lastAnswer.value
  lastAnswer.value = ''
  const lastIdx = messages.value.findLastIndex(m => m.role === 'candidate')
  if (lastIdx !== -1) messages.value.splice(lastIdx, 1)
  await handleSubmit()
}
</script>

<style scoped>
.interview-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  background: var(--c-bg);
}

/* 准备动画 */
.prepare-overlay {
  position: fixed; inset: 0;
  background: var(--c-bg);
  display: flex; align-items: center; justify-content: center; z-index: 200;
}
.prepare-card {
  text-align: center; padding: 56px 48px;
  background: var(--c-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--c-border);
  box-shadow: var(--shadow-xl);
  animation: prepareIn 0.4s var(--ease-out);
}
@keyframes prepareIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.ai-face-large { animation: faceFloat 2.5s ease-in-out infinite; }
@keyframes faceFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.prepare-title {
  margin-top: var(--space-6);
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  letter-spacing: -0.01em;
}
.prepare-tip {
  color: var(--c-text-secondary);
  margin-top: var(--space-2);
  font-size: var(--text-base);
  transition: opacity 0.3s;
}
.prepare-subtitle {
  color: var(--c-text-muted);
  font-size: var(--text-xs);
  margin-top: var(--space-3);
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
}
.prepare-progress {
  width: 280px; height: 3px;
  background: var(--c-border-light);
  border-radius: 0;
  margin: var(--space-6) auto 0;
  overflow: hidden;
}
.prepare-bar {
  height: 100%;
  background: var(--c-primary);
  border-radius: 0;
  transition: width 0.3s ease;
}

/* 顶部 */
.interview-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--space-3) var(--space-5);
  background: var(--c-surface);
  border-bottom: 2px solid var(--c-border);
  position: sticky; top: 0; z-index: 10;
}
.header-left { display: flex; align-items: center; gap: var(--space-3); }
.header-ai-mark {
  width: 28px; height: 28px;
  border-radius: var(--radius-sm);
  background: var(--c-primary);
  color: white;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
}
.header-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 400;
}
.progress {
  color: var(--c-text-muted);
  font-weight: 500;
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
}
.exit-btn { padding: 4px 14px; font-size: var(--text-xs); }

/* 聊天 */
.chat-area {
  flex: 1; overflow-y: auto;
  padding: var(--space-6) var(--space-5);
  display: flex; flex-direction: column; gap: var(--space-5);
}
.message {
  display: flex; align-items: flex-start; gap: var(--space-3);
  animation: msgIn 0.3s var(--ease-out);
}
@keyframes msgIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.message.interviewer { justify-content: flex-start; }
.message.candidate { justify-content: flex-end; }

/* 头像 */
.avatar-col { flex-shrink: 0; margin-top: 2px; }
.ai-avatar-wrap {
  width: 36px; height: 36px;
  border-radius: 50%;
  overflow: hidden;
}
.ai-avatar-wrap.thinking { animation: avatarPulse 2s ease-in-out infinite; }
@keyframes avatarPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(37,99,235,0); }
  50% { box-shadow: 0 0 0 3px rgba(37,99,235,0.15); }
}
.user-avatar {
  width: 36px; height: 36px; border-radius: 50%; object-fit: cover;
  border: 1px solid var(--c-border);
}
.user-avatar-placeholder {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--c-primary);
  color: white; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600;
  font-family: var(--font-mono);
}

/* 气泡 */
.bubble {
  max-width: 72%;
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  line-height: 1.75;
}
.interviewer .bubble {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-bottom-left-radius: 0;
}
.candidate .bubble {
  background: var(--c-primary);
  color: white;
  border-bottom-right-radius: 0;
}
.thinking-bubble {
  color: var(--c-text-muted);
  font-style: italic;
  background: var(--c-bg) !important;
  border-color: var(--c-border-light) !important;
}
.dot-animation .dots::after { content: ''; animation: dots 1.5s steps(4, end) infinite; }
@keyframes dots {
  0% { content: ''; } 25% { content: '.'; } 50% { content: '..'; } 75% { content: '...'; } 100% { content: ''; }
}
.streaming-content { display: inline; }
.cursor-blink {
  display: inline;
  animation: blink 0.8s step-end infinite;
  color: var(--c-primary);
  font-size: 13px;
  margin-left: 2px;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.bubble-score {
  margin-top: var(--space-2);
  padding-top: var(--space-2);
  border-top: 1px solid rgba(255,255,255,0.2);
  font-size: var(--text-xs);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}
.interviewer .bubble-score {
  border-top-color: var(--c-border-light);
  color: var(--c-primary);
}
.error-bubble {
  border: 1px solid var(--c-danger) !important;
  background: var(--c-danger-light) !important;
  color: var(--c-danger);
}

/* 输入 */
.input-area {
  padding: var(--space-4) var(--space-5);
  background: var(--c-surface);
  border-top: 2px solid var(--c-border);
  display: flex; gap: var(--space-3); align-items: flex-end;
}
.input-area textarea {
  flex: 1; resize: none; font-family: inherit;
  border-radius: var(--radius-sm);
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-base);
  line-height: 1.6;
  transition: border-color var(--duration-fast);
}
.input-area textarea:focus {
  border-color: var(--c-primary);
  box-shadow: var(--shadow-glow);
}
.send-btn {
  padding: var(--space-3) var(--space-6);
  font-weight: 600;
  letter-spacing: 0.04em;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  flex-shrink: 0;
}
.input-area.finished {
  justify-content: center; align-items: center;
  padding: var(--space-8); gap: var(--space-4);
}
.finished-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 400;
}
.report-btn {
  display: inline-block;
  padding: var(--space-3) var(--space-8);
  border-radius: var(--radius-sm);
  font-weight: 600;
  letter-spacing: 0.04em;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

/* 响应式 */
@media (max-width: 768px) {
  .bubble { max-width: 88%; font-size: var(--text-sm); }
  .interview-header { padding: var(--space-2) var(--space-4); }
  .chat-area { padding: var(--space-4); }
  .input-area { padding: var(--space-3) var(--space-4); }
  .prepare-card { padding: 36px 28px; margin: var(--space-4); }
}
</style>
