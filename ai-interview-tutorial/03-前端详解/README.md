# 第三章：前端详解

## 3.1 技术栈与项目结构

前端基于 **Vue 3 + Vite 5** 构建，使用 Composition API、Pinia 状态管理和 Vue Router 路由。

```
ai-interview-frontend/
├── src/
│   ├── views/              # 页面组件
│   │   ├── Login.vue       # 登录
│   │   ├── Register.vue    # 注册
│   │   ├── Dashboard.vue   # 仪表盘
│   │   ├── ResumeUpload.vue # 简历上传
│   │   ├── Interview.vue   # 面试对话页（核心）
│   │   ├── Report.vue      # 评估报告
│   │   ├── Profile.vue     # 个人中心
│   │   └── admin/          # 管理后台页面
│   │       ├── AdminLogin.vue
│   │       ├── AdminLayout.vue
│   │       ├── Dashboard.vue
│   │       ├── Users.vue
│   │       ├── Interviews.vue
│   │       ├── InterviewDetail.vue
│   │       ├── LLMConfig.vue
│   │       ├── QuestionBank.vue
│   │       ├── DocumentManagement.vue
│   │       ├── DocumentDetail.vue
│   │       └── PositionTemplates.vue
│   ├── api/                # API 调用层
│   │   ├── request.js      # Axios 实例 + 拦截器
│   │   ├── auth.js         # 认证 API
│   │   ├── resume.js       # 简历 API
│   │   ├── interview.js    # 面试 API
│   │   ├── user.js         # 用户 API
│   │   ├── adminApi.js     # 管理端 API
│   │   ├── adminRequest.js # 管理端 Axios 实例
│   │   ├── knowledge.js    # 知识库 API
│   │   ├── llmConfig.js    # LLM 配置 API
│   │   ├── positionTemplate.js
│   │   └── questionBank.js
│   ├── stores/             # Pinia 状态管理
│   │   ├── auth.js         # 用户认证状态
│   │   ├── adminAuth.js    # 管理员认证状态
│   │   └── toast.js        # 提示消息
│   └── router/
│       └── index.js        # 路由配置 + 守卫
├── vite.config.js
└── package.json
```

## 3.2 Vite 配置

```js
// vite.config.js
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8006',  // 后端地址
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://127.0.0.1:8006',  // 静态文件
        changeOrigin: true
      }
    }
  }
})
```

**关键点**：开发环境下，`/api` 和 `/uploads` 请求通过 Vite 代理转发到后端，避免跨域问题。

## 3.3 路由设计

```js
// router/index.js
const routes = [
  // 公开页面
  { path: '/login',    name: 'Login',    component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },

  // 需要登录的页面
  { path: '/dashboard',      name: 'Dashboard',      meta: { auth: true }, ... },
  { path: '/resume/upload',  name: 'ResumeUpload',   meta: { auth: true }, ... },
  { path: '/interview/:id',  name: 'Interview',      meta: { auth: true }, ... },
  { path: '/interview/:id/report', name: 'Report',    meta: { auth: true }, ... },
  { path: '/profile',        name: 'Profile',         meta: { auth: true }, ... },

  // 管理后台
  { path: '/admin/login', name: 'AdminLogin', ... },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { admin: true },
    children: [
      { path: 'dashboard',          name: 'AdminDashboard', ... },
      { path: 'users',              name: 'AdminUsers', ... },
      { path: 'interviews',         name: 'AdminInterviews', ... },
      { path: 'interviews/:id',     name: 'AdminInterviewDetail', ... },
      { path: 'llm-config',         name: 'LLMConfig', ... },
      { path: 'question-bank',      name: 'QuestionBank', ... },
      { path: 'documents',          name: 'Documents', ... },
      { path: 'documents/:id',      name: 'DocumentDetail', ... },
      { path: 'position-templates', name: 'PositionTemplates', ... },
    ]
  },

  { path: '/', redirect: '/dashboard' }
]
```

### 路由守卫

```js
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const adminStore = useAdminAuthStore()

  // 管理后台路由 → 检查管理员登录
  if (to.meta.admin && !adminStore.isLoggedIn) {
    next('/admin/login')
    return
  }

  // 用户端路由 → 检查用户登录
  if (to.meta.auth && !authStore.isLoggedIn) {
    next('/login')
    return
  }

  next()
})
```

管理后台和用户端使用**独立的认证状态**，互不影响。

## 3.4 状态管理 (Pinia)

### 用户认证 Store (`stores/auth.js`)

```js
export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const userEmail = ref(localStorage.getItem('userEmail') || '')
  const userId = ref(localStorage.getItem('userId') || '')
  const userName = ref(localStorage.getItem('userName') || '')
  const userAvatar = ref(localStorage.getItem('userAvatar') || '')

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(data) {
    // 设置 token 和用户信息，同步到 localStorage
    token.value = data.access_token
    // ...
    localStorage.setItem('token', data.access_token)
  }

  function logout() {
    // 清空所有状态和 localStorage
    token.value = ''
    localStorage.removeItem('token')
    // ...
  }

  return { token, refreshToken, userEmail, userId, userName, userAvatar,
           isLoggedIn, setAuth, setUserInfo, logout }
})
```

**设计要点**：
- 使用 Composition API 风格（`setup` 函数）
- 持久化到 `localStorage`，刷新页面不丢失登录状态
- `isLoggedIn` 是计算属性，通过 `!!token.value` 判断

## 3.5 API 请求层

### Axios 实例 (`api/request.js`)

```js
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000  // 60 秒超时（AI 请求可能较慢）
})

// 请求拦截器：自动携带 token
api.interceptors.request.use(config => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  response => {
    const data = response.data
    if (data.code === 200) {
      return data.data  // 直接返回业务数据
    }
    return Promise.reject(new Error(data.message || '请求失败'))
  },
  error => {
    // 401/403 → 自动登出跳转登录页
    if (error.response?.status === 403 || error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.push('/login')
    }
    // 处理 FastAPI 422 验证错误
    // ...
  }
)
```

**设计模式**：
- 请求拦截器自动注入 `Authorization` header
- 响应拦截器解包 `ApiResponse`，成功时直接返回 `data.data`
- 401/403 自动登出，用户无感知地回到登录页
- 统一错误消息处理，包括 FastAPI 的 422 验证错误

### 面试 API (`api/interview.js`)

```js
// 普通请求：使用 Axios
export function startInterview(data) {
  return api.post('/interviews/start', data)
}

// 流式请求：使用原生 fetch + ReadableStream
export async function submitAnswerStream(interviewId, answer, onChunk, onDone) {
  const response = await fetch(`/api/v1/interviews/${interviewId}/answer/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authStore.token}`
    },
    body: JSON.stringify({ answer })
  })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    // 解析 SSE 格式
    const lines = buffer.split('\n')
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'chunk') onChunk(data.content)
        if (data.type === 'done') onDone(data)
      }
    }
  }
}
```

**为什么流式用 `fetch` 而不是 `axios`？**

Axios 不原生支持 `ReadableStream` 的逐步读取。SSE 流式响应需要通过 `response.body.getReader()` 逐块消费，这是 Fetch API 的能力。普通请求仍然用 Axios 保持一致性。

## 3.6 核心页面

### 面试页面 (`views/Interview.vue`)

面试页面是系统最复杂的前端组件，包含以下状态：

```
preparing (准备动画)
    ↓
面试进行中
    ├── messages: 已完成的消息列表
    ├── streamingText: 当前流式输出的文本
    ├── thinking: AI 思考中状态
    ├── currentIndex: 当前题目索引
    └── totalQuestions: 总题数
    ↓
完成 → 跳转到 Report 页面
```

#### 准备动画

进入面试页面后，先展示一个带进度条的准备动画，等待 AI 生成面试题目：

```vue
<div v-if="preparing" class="prepare-overlay">
  <div class="prepare-card">
    <h2>面试即将开始</h2>
    <p>{{ prepareTip }}</p>
    <div class="prepare-progress">
      <div class="prepare-bar" :style="{ width: preparePercent + '%' }"></div>
    </div>
    <p>AI 正在为你准备面试题目...</p>
  </div>
</div>
```

#### 流式消息展示

面试过程中，AI 评估通过 SSE 流式推送，前端实时显示：

```vue
<!-- 已完成的消息 -->
<div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
  <div class="bubble">
    <div class="bubble-content" v-html="renderContent(msg.content)"></div>
    <div v-if="msg.score" class="bubble-score">⭐ {{ msg.score }}/10</div>
  </div>
</div>

<!-- 流式输出中 -->
<div v-if="streamingText" class="message interviewer">
  <div class="bubble">
    <div class="bubble-content" v-html="renderContent(streamingText)"></div>
    <span class="cursor-blink">▊</span>
  </div>
</div>
```

#### 评分提取

流式输出中，AI 先输出评语文本，最后附上 JSON 评分。前端通过正则匹配分离：

```js
function processStreamingText(text) {
  // 匹配末尾的 JSON 评分块
  const jsonMatch = text.match(/\{[\s\S]*"score"[\s\S]*\}/)
  if (jsonMatch) {
    const displayText = text.replace(jsonMatch[0], '').trim()
    const scoreData = JSON.parse(jsonMatch[0])
    return { displayText, score: scoreData.score }
  }
  return { displayText: text, score: null }
}
```

### 报告页面 (`views/Report.vue`)

面试完成后展示综合评估报告，包含：
- 总体评分
- 各维度评分（技术能力、沟通能力、逻辑思维等）
- 优势与不足分析
- 录用建议

### 简历上传页面 (`views/ResumeUpload.vue`)

上传 PDF 简历并选择目标岗位，上传后 AI 自动解析并展示结构化信息。

## 3.7 管理后台

管理后台嵌入在同一前端项目中，通过 `/admin` 路径访问，使用 `AdminLayout.vue` 作为布局容器。

### 功能模块

| 路径 | 组件 | 功能 |
|------|------|------|
| `/admin/dashboard` | Dashboard.vue | 数据概览 |
| `/admin/users` | Users.vue | 用户管理 |
| `/admin/interviews` | Interviews.vue | 面试记录管理 |
| `/admin/interviews/:id` | InterviewDetail.vue | 面试详情查看 |
| `/admin/llm-config` | LLMConfig.vue | LLM 提供商/模型管理 |
| `/admin/question-bank` | QuestionBank.vue | 题库管理 |
| `/admin/documents` | DocumentManagement.vue | 知识库文档管理 |
| `/admin/documents/:id` | DocumentDetail.vue | 文档详情/分块查看 |
| `/admin/position-templates` | PositionTemplates.vue | 岗位面试模板管理 |

管理端使用独立的 Axios 实例（`adminRequest.js`）和认证 Store（`adminAuth`），与用户端完全隔离。

## 3.8 依赖说明

```json
{
  "dependencies": {
    "vue": "^3.4.0",           // 前端框架
    "vue-router": "^4.3.0",    // 路由
    "pinia": "^2.1.0",         // 状态管理
    "axios": "^1.7.0"          // HTTP 客户端
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",  // Vue SFC 支持
    "vite": "^5.4.0"                 // 构建工具
  }
}
```

极简依赖，没有引入 UI 框架（如 Element Plus），所有样式手写，保持轻量。

---

> **上一章**：[02-后端详解](../02-后端详解/README.md)
> **下一章**：[04-核心流程](../04-核心流程/README.md)
