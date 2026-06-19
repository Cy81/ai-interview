# 第四章：核心流程

本章深入剖析系统的核心业务流程，从用户操作到代码执行的完整链路。

## 4.1 用户认证流程

### 注册 → 登录 → 访问受保护页面

```
用户填写邮箱+密码
    │
    ▼
POST /api/v1/auth/register
    │
    ├─ 校验邮箱是否已注册
    ├─ 密码 bcrypt 哈希
    ├─ 写入 users 表
    └─ 返回成功
    │
    ▼
POST /api/v1/auth/login
    │
    ├─ 校验邮箱+密码
    ├─ 生成 Access Token (30min) + Refresh Token (7d)
    └─ 返回 { access_token, refresh_token, user: {...} }
    │
    ▼
前端 authStore.setAuth(data)
    │
    ├─ token 存入 ref + localStorage
    └─ isLoggedIn 计算属性变为 true
    │
    ▼
路由守卫放行 → 进入 Dashboard
```

### Token 刷新

当 Access Token 过期时，前端拦截器检测到 401，使用 Refresh Token 请求新的 Access Token，实现无感续期。

## 4.2 简历上传与解析流程

```
用户上传 PDF + 选择目标岗位
    │
    ▼
POST /api/v1/resumes/upload
    │  (multipart/form-data)
    ▼
ResumeService.upload_and_parse()
    │
    ├─ 1. 保存文件到 uploads/resumes/{user_id}/
    ├─ 2. 创建 Resume 记录 (status="parsing")
    ├─ 3. pdfplumber 提取 PDF 文本
    │     └─ _extract_pdf_text(file_path) → raw text
    ├─ 4. AIService.parse_resume(raw_text)
    │     └─ Prompt: "将以下简历文本解析为 JSON 格式，包含：
    │         name, email, phone, education[], experience[],
    │         skills[], projects[], certifications[]"
    │     └─ 返回结构化 JSON
    ├─ 5. AIService.analyze_resume(parsed_resume, target_position)
    │     └─ Prompt: "分析该简历申请 {target_position} 的匹配度，
    │         返回：score(0-100), strengths[], weaknesses[], suggestions[]"
    │     └─ 返回分析 JSON
    ├─ 6. 更新 Resume 记录
    │     ├─ parsed_content = JSON.stringify(parsed_resume)
    │     ├─ analysis = JSON.stringify(analysis)
    │     └─ status = "completed"
    └─ 7. 返回简历数据给前端
```

**异常处理**：任何步骤失败，Resume 的 `status` 设为 `"failed"`，前端可显示错误信息并允许重试。

## 4.3 面试完整流程

这是系统最核心的流程，涉及多轮对话、AI 评估和最终报告生成。

### 4.3.1 开始面试

```
前端 POST /api/v1/interviews/start
    body: { resume_id, target_position, difficulty, total_questions }
    │
    ▼
InterviewService.start_interview()
    │
    ├─ 1. 校验简历存在且 status="completed"
    ├─ 2. AIService.generate_questions()
    │     └─ Prompt: 根据简历内容和目标岗位，生成 N 道面试题
    │     └─ 返回 [{question, category, expected_points}, ...]
    ├─ 3. 创建 Interview 记录
    │     ├─ status = "in_progress"
    │     ├─ questions_data = 生成的题目 JSON
    │     └─ current_question_index = 0
    └─ 4. 创建第一条 InterviewMessage
          ├─ role = "interviewer"
          └─ content = 第一道面试题
    │
    ▼
前端收到响应 → 跳转到 /interview/{id}
    │
    ▼
Interview.vue 进入 preparing 状态
    ├─ 展示准备动画 + 进度条
    ├─ 加载面试数据和历史消息
    └─ 准备完成 → 进入面试对话界面
```

### 4.3.2 回答问题（流式模式）

```
用户输入回答 → 点击提交
    │
    ▼
前端调用 submitAnswerStream()
    │
    ├─ fetch POST /api/v1/interviews/{id}/answer/stream
    ├─ 前端显示 thinking 状态（AI 思考中动画）
    │
    ▼
后端 InterviewService.submit_answer_stream()
    │
    ├─ 1. 校验面试状态和题目索引
    ├─ 2. 保存用户回答消息 (role="candidate")
    ├─ 3. 构建上下文：
    │     ├─ 当前题目
    │     ├─ 用户回答
    │     ├─ 简历上下文
    │     └─ 历史对话记录
    ├─ 4. AIService.evaluate_answer_stream()
    │     └─ 流式调用 DeepSeek API
    │     └─ 逐块 yield SSE 事件
    │
    ▼ (SSE 事件流)
前端 ReadableStream 逐块读取
    │
    ├─ type="chunk" → 追加到 streamingText
    │   └─ 用户看到评语逐字出现
    │
    ├─ type="chunk" (包含 JSON) → 处理评分
    │   └─ 正则匹配 {"score": N} → 显示评分
    │
    └─ type="done" → 面试完成或进入下一题
        │
        ├─ 有 next_question:
        │   ├─ 保存 AI 评语消息 (role="interviewer")
        │   ├─ 保存下一题消息 (role="interviewer")
        │   └─ currentIndex++
        │
        └─ 无 next_question (最后一题):
            ├─ AIService.generate_report()
            │   └─ Prompt: 根据所有问答和评分生成综合报告
            │   └─ 返回 { overall_score, dimensions[], summary, ... }
            ├─ 更新 Interview: status="completed", report=JSON
            └─ 前端跳转到 Report 页面
```

### 4.3.3 SSE 通信细节

**后端发送格式**：

```
data: {"type": "chunk", "content": "你的回答展现了扎实的基础知识"}

data: {"type": "chunk", "content": "，在项目经验方面..."}

data: {"type": "chunk", "content": "\n\n{\"score\": 7.5}"}

data: {"type": "done", "next_question": {"content": "请介绍一下...", "index": 2}}
```

**前端解析逻辑**：

```js
// api/interview.js
for (const line of lines) {
  if (line.startsWith('data: ')) {
    const data = JSON.parse(line.slice(6))
    if (data.type === 'chunk') {
      onChunk(data.content)  // 累加到 streamingText
    } else if (data.type === 'done') {
      onDone(data)  // 处理完成事件
    } else if (data.type === 'error') {
      throw new Error(data.content)
    }
  }
}
```

### 4.3.4 面试状态机

```
                    ┌─────────────┐
                    │   开始面试   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
              ┌────►│  回答第 N 题 │◄────┐
              │     └──────┬──────┘     │
              │            │             │
              │            ▼             │
              │     ┌─────────────┐     │
              │     │  AI 评估中   │     │
              │     └──────┬──────┘     │
              │            │             │
              │     ┌──────┴──────┐     │
              │     │             │     │
              │     ▼             ▼     │
              │  还有题目     最后一题    │
              │     │             │     │
              │     ▼             ▼     │
              │  显示下一题   生成报告    │
              │     │             │     │
              └─────┘             ▼     │
                           ┌───────────┐
                           │ 面试完成   │
                           └─────┬─────┘
                                 │
                                 ▼
                           ┌───────────┐
                           │ 查看报告   │
                           └───────────┘
```

## 4.4 AI Prompt 设计

### 简历解析 Prompt

```
你是一个专业的简历解析助手。请将以下简历文本解析为 JSON 格式：
{
  "name": "姓名",
  "email": "邮箱",
  "phone": "电话",
  "education": [{ "school": "", "degree": "", "major": "", "start": "", "end": "" }],
  "experience": [{ "company": "", "position": "", "start": "", "end": "", "description": "" }],
  "skills": ["技能1", "技能2"],
  "projects": [{ "name": "", "description": "", "tech": [] }]
}
只返回 JSON，不要其他文字。
```

### 面试出题 Prompt

```
你是一个专业的技术面试官。根据以下信息生成面试题：

候选人简历：{parsed_resume_json}
目标岗位：{target_position}
难度：{difficulty}
题目数量：{count}

要求：
1. 题目应针对候选人的经历和技能
2. 包含基础题、项目深挖题、场景题
3. 实习岗位侧重基础和学习能力，不考察工作经验

返回 JSON 数组：[{ "question": "", "category": "", "expected_points": [] }]
```

### 回答评估 Prompt（流式版本）

```
你是一个专业的面试官。评估候选人的回答：

问题：{question}
候选人回答：{answer}
简历背景：{resume_context}
历史对话：{chat_history}

请先用 2-3 句话给出评语，然后在最后一行输出 JSON 评分：
{"score": 7.5, "feedback": "简短评价", "strengths": [], "improvements": []}
```

**巧妙之处**：评语和评分合并到一个响应中，前端通过正则分离，实现"先看评语再看分数"的渐进体验。

## 4.5 动态 LLM 切换流程

```
管理员在 /admin/llm-config 页面操作
    │
    ├─ 添加 LLM Provider（名称、Base URL、API Key）
    ├─ 添加 LLM Model（关联 Provider、模型名称）
    └─ 设置某个模型为激活状态
    │
    ▼
POST /api/v1/backoffice/llm-config/...
    │
    ▼
LLMConfigService 更新数据库
    │
    └─ 调用 AIService.invalidate_config_cache()
       └─ 清除缓存，下次请求重新从数据库加载
    │
    ▼
下一个 AI 请求到来
    │
    ▼
AIService._get_client()
    │
    ├─ 缓存已失效 → 从数据库加载新配置
    ├─ 创建新的 AsyncOpenAI(base_url=..., api_key=...)
    └─ 使用新模型进行对话
```

**效果**：管理员可以在不停机的情况下切换 AI 模型，例如从 DeepSeek 切换到 GPT-4，60 秒内生效。

## 4.6 评估报告生成

面试完成后，`AIService.generate_report()` 收集所有问答和评分，生成综合报告：

```
输入：
{
  "parsed_resume": {...},
  "target_position": "前端开发工程师",
  "questions_and_scores": [
    { "question": "...", "answer": "...", "score": 7.5, "feedback": "..." },
    { "question": "...", "answer": "...", "score": 8.0, "feedback": "..." },
    ...
  ]
}

输出：
{
  "overall_score": 7.6,
  "dimensions": [
    { "name": "技术能力", "score": 8.0, "comment": "..." },
    { "name": "沟通表达", "score": 7.0, "comment": "..." },
    { "name": "逻辑思维", "score": 7.5, "comment": "..." },
    { "name": "项目经验", "score": 7.5, "comment": "..." }
  ],
  "strengths": ["基础扎实", "项目经验丰富"],
  "weaknesses": ["沟通可以更简洁", "缺少大规模项目经验"],
  "suggestion": "建议加强...",
  "hire_recommendation": "推荐录用"
}
```

## 4.7 实习岗位的特殊处理

`AIService` 会检测 `target_position` 是否包含"实习"关键词，如果是，调整 Prompt 策略：

- 不因缺少工作经验而扣分
- 侧重考察基础知识和学习能力
- 评估标准适当放宽
- 在报告中注明"实习岗位评估标准"

这个设计使系统既能服务社招也能服务校招场景。

---

> **上一章**：[03-前端详解](../03-前端详解/README.md)
> **下一章**：[05-扩展与部署](../05-扩展与部署/README.md)
