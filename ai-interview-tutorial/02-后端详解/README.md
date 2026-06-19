# 第二章：后端详解

## 2.1 入口与应用启动

### `main.py` — 启动入口

```python
import uvicorn
from app.route.route import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
```

使用 `uvicorn` 启动 FastAPI 应用，开发模式下开启热重载。

### `route/route.py` — 应用工厂

`create_app()` 是应用工厂函数，负责：

1. **创建 FastAPI 实例**，配置 `lifespan` 生命周期管理
2. **注册 CORS 中间件**，开发环境允许所有来源
3. **通过路由注册中心注册所有路由**（`register_routes`）
4. **挂载静态文件**（`/uploads` 目录用于简历文件访问）
5. **注册全局异常处理器**（`APIException`、`HTTPException`、`RequestValidationError`）

生命周期管理（`lifespan`）在应用启动时初始化日志系统，关闭时清理数据库连接、Redis 连接和线程池。

## 2.2 配置管理

### `core/config.py` — Settings 类

使用 `pydantic_settings.BaseSettings` 管理所有配置，支持从 `.env` 文件加载：

```python
class Settings(BaseSettings):
    ENV: str = "development"
    API_V1_STR: str = "/api/v1"
    API_PORT: int = 8001

    # PostgreSQL
    POSTGRES_USER: str = "demo"
    POSTGRES_PASSWORD: str = "demo123"
    POSTGRES_HOST: str = "192.168.110.90"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "demo"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # DeepSeek (默认 LLM)
    DEEPSEEK_API_KEY: str = "your-deepseek-api-key"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    class Config:
        env_file = ".env"
```

全局单例 `settings = Settings()` 在整个应用中引用。

**关键点**：配置值优先从环境变量读取，缺失时使用默认值。生产环境必须在 `.env` 中覆盖 `SECRET_KEY`、数据库密码和 API Key。

## 2.3 路由注册中心

### `route/router_registry.py`

采用 **声明式路由配置**，避免手动逐个注册路由器：

```python
class RouteConfig:
    def __init__(self, module_path: str, prefix: str, tags: List[str]):
        self.module_path = module_path
        self.prefix = prefix
        self.tags = tags

CLIENT_ROUTES = [
    RouteConfig("app.api.client.v1.auth",      "/api/v1/auth",      ["client-auth"]),
    RouteConfig("app.api.client.v1.resume",    "/api/v1/resumes",   ["client-resume"]),
    RouteConfig("app.api.client.v1.interview", "/api/v1/interviews", ["client-interview"]),
    # ...
]

BACKOFFICE_ROUTES = [
    RouteConfig("app.api.backoffice.v1.users",          "/api/v1/backoffice/users",          ["backoffice-users"]),
    RouteConfig("app.api.backoffice.v1.interviews",      "/api/v1/backoffice/interviews",     ["backoffice-interviews"]),
    RouteConfig("app.api.backoffice.v1.llm_config",      "/api/v1/backoffice/llm-configs",    ["backoffice-llm-config"]),
    # ...
]
```

`register_routes()` 函数动态 `__import__` 模块，获取其中的 `router` 对象，调用 `app.include_router()` 完成注册。

**新增 API 模块只需**：
1. 在对应目录下创建新文件并定义 `router`
2. 在 `router_registry.py` 中添加一行 `RouteConfig`

## 2.4 数据模型

### 用户模型 (`models/user.py`)

```python
class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar = Column(String(255), nullable=True)
    gender = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    university = Column(String(255), nullable=True)
    career_goal = Column(String(255), nullable=True)
    contract_types = Column(JSON, nullable=True)
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(TIMESTAMP, nullable=True)
    last_active_at = Column(TIMESTAMP, default=func.now())
```

密码使用 `passlib` + `bcrypt` 哈希存储，提供 `get_password_hash()` 和 `verify_password()` 方法。

### 简历模型 (`models/resume.py`)

```python
class Resume(BaseModel):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    parsed_content = Column(Text, nullable=True)    # AI 解析的 JSON
    analysis = Column(Text, nullable=True)           # AI 分析 JSON
    target_position = Column(String(255), nullable=True)
    status = Column(String(20), default="pending")   # pending/parsing/completed/failed
```

### 面试模型 (`models/interview.py`)

```python
class Interview(BaseModel):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    target_position = Column(String(255), nullable=True)
    difficulty = Column(String(20), default="medium")     # easy/medium/hard
    total_questions = Column(Integer, default=5)
    status = Column(String(20), default="in_progress")    # in_progress/completed
    current_question_index = Column(Integer, default=0)
    questions_data = Column(JSONB, nullable=True)         # AI 生成的题目
    overall_score = Column(DECIMAL(3, 1), nullable=True)
    report = Column(Text, nullable=True)                  # 最终报告 JSON
```

**关联关系**：
- `User` 1:N `Resume`（一个用户可上传多份简历）
- `User` 1:N `Interview`（一个用户可进行多次面试）
- `Resume` 1:N `Interview`（一份简历可关联多次面试）
- `Interview` 1:N `InterviewMessage`（一次面试有多条消息）

## 2.5 核心服务层

### AI 服务 (`services/client/ai_service.py`)

这是系统的核心，负责所有与 LLM 的交互。关键设计：

#### 动态 LLM 配置

```python
_cached_client: Optional[AsyncOpenAI] = None
_cached_model: Optional[str] = None
_cache_loaded_at: float = 0
_CACHE_TTL = 60  # 60 秒缓存
_cache_lock = asyncio.Lock()

class AIService:
    @staticmethod
    async def _get_client() -> Tuple[AsyncOpenAI, str]:
        """获取 LLM 客户端。优先从数据库加载激活的配置，60 秒 TTL 缓存，回退到 .env 的 DeepSeek 配置。"""
```

**工作流程**：
1. 检查缓存是否有效（60 秒内）
2. 有效 → 返回缓存的客户端和模型名
3. 过期 → 从数据库查询 `is_active=True` 的 `LLMProvider` + `LLMModel`
4. 数据库无配置 → 回退到 `.env` 中的 `DEEPSEEK_*` 配置
5. 更新缓存

管理员在后台修改 LLM 配置后，调用 `invalidate_config_cache()` 立即生效。

#### 核心方法

| 方法 | 功能 |
|------|------|
| `_chat(messages, temperature)` | 同步对话补全 |
| `_chat_stream(messages, temperature)` | 流式对话补全（yield chunks） |
| `parse_resume(resume_text)` | 解析简历文本为结构化 JSON |
| `analyze_resume(parsed_resume, target_position)` | 分析简历优劣势 |
| `generate_questions(parsed_resume, position, difficulty, count)` | 生成面试题目 |
| `evaluate_answer(...)` | 评估回答，返回评分和反馈 |
| `evaluate_answer_stream(...)` | 流式评估，先输出评语再输出 JSON 评分 |
| `generate_report(...)` | 生成综合评估报告 |

#### 流式输出的巧妙设计

`evaluate_answer_stream()` 的输出格式：先输出纯文本评语，最后附上 JSON 评分块。前端通过正则匹配 `{"score": ...}` 来分离评语和分数，实现"边看评语边算分"的体验。

### 简历服务 (`services/client/resume_service.py`)

```python
class ResumeService:
    @staticmethod
    async def upload_and_parse(db, user_id, file_content, file_name, target_position):
        # 1. 保存文件到 uploads/resumes/
        # 2. 创建 Resume 记录 (status="parsing")
        # 3. pdfplumber 提取 PDF 文本
        # 4. AIService.parse_resume() 解析结构化数据
        # 5. AIService.analyze_resume() 分析优劣势
        # 6. 更新 status="completed" 或 "failed"
```

### 面试服务 (`services/client/interview_service.py`)

```python
class InterviewService:
    @staticmethod
    async def start_interview(db, user_id, resume_id, target_position, difficulty, total_questions):
        # 1. 校验简历存在且已解析
        # 2. AIService.generate_questions() 生成题目
        # 3. 创建 Interview 记录
        # 4. 创建第一条 InterviewMessage (role="interviewer"，第一道题)

    @staticmethod
    async def submit_answer_stream(db, user_id, interview_id, answer):
        # 1. 校验面试状态
        # 2. 保存用户回答消息
        # 3. AIService.evaluate_answer_stream() 流式评估
        # 4. yield SSE chunk 事件
        # 5. 评估完成：
        #    - 如果还有下一题 → yield done + next_question
        #    - 如果最后一题 → AIService.generate_report() → yield done + report
```

## 2.6 API 路由层

### Client API 示例

以面试接口为例（`api/client/v1/interview.py`）：

```python
router = APIRouter()

@router.post("/start")
async def start_interview(data: StartInterviewRequest, ...):
    return await interview_service.start_interview(db, user_id, ...)

@router.post("/{interview_id}/answer")
async def submit_answer(interview_id: int, data: AnswerRequest, ...):
    return await interview_service.submit_answer(db, user_id, interview_id, data.answer)

@router.post("/{interview_id}/answer/stream")
async def submit_answer_stream(interview_id: int, data: AnswerRequest, ...):
    return StreamingResponse(
        interview_service.submit_answer_stream(db, user_id, interview_id, data.answer),
        media_type="text/event-stream"
    )
```

### SSE 流式响应格式

```
data: {"type": "chunk", "content": "你的回答"}

data: {"type": "chunk", "content": "整体思路不错，"}

data: {"type": "chunk", "content": "但可以更具体..."}

data: {"type": "chunk", "content": "\n\n{\"score\": 7.5, \"feedback\": \"...\"}"}

data: {"type": "done", "next_question": {...}, "current_index": 2}
```

## 2.7 认证与安全

### `core/security.py`

- **JWT Token**：使用 `python-jose` 生成/验证
- **双 Token 机制**：Access Token（30 分钟）+ Refresh Token（7 天）
- **密码哈希**：`passlib` + `bcrypt`
- **路由守卫**：依赖注入检查 token 有效性

### 依赖注入示例

```python
from app.core.security import get_current_user

@router.get("/me")
async def get_profile(user = Depends(get_current_user)):
    return user
```

## 2.8 数据库迁移

使用 Alembic 管理数据库版本：

```bash
# 生成迁移文件
alembic revision --autogenerate -m "add_new_table"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 2.9 异常处理

全局异常处理器统一返回 `ApiResponse` 格式：

```python
class APIException(HTTPException):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
```

返回格式：
```json
{
  "code": 400,
  "message": "简历尚未解析完成",
  "data": null
}
```

## 2.10 目录结构速查

```
app/
├── api/client/v1/          # 用户端 API
│   ├── auth.py             # 认证（登录/注册/刷新token）
│   ├── resume.py           # 简历（上传/获取）
│   ├── interview.py        # 面试（开始/答题/报告）
│   ├── config.py           # 配置健康检查
│   ├── demo.py             # 演示接口
│   ├── waiting_list.py     # 等待列表
│   └── aws.py              # S3 文件上传
├── api/backoffice/v1/      # 管理端 API
│   ├── auth.py, admin.py   # 管理员认证
│   ├── users.py            # 用户管理
│   ├── interviews.py       # 面试管理
│   ├── llm_config.py       # LLM 配置
│   ├── question_bank.py    # 题库管理
│   ├── knowledge.py        # 知识库管理
│   └── position_templates.py # 岗位模板
├── services/client/        # 用户端业务逻辑
├── services/backoffice/    # 管理端业务逻辑
├── services/common/        # 公共服务
├── services/               # 顶层服务
├── models/                 # 数据库模型
├── schemas/                # Pydantic Schema
├── route/                  # 应用工厂 + 路由注册
├── core/                   # 配置/安全/日志/Celery
├── db/                     # 数据库连接
├── exceptions/             # 自定义异常
├── configs/                # 文档 App 配置
├── schedule/               # 定时任务
├── scripts/                # 种子脚本
└── common/                 # 日志消费等
```

---

> **上一章**：[01-项目概览](../01-项目概览/README.md)
> **下一章**：[03-前端详解](../03-前端详解/README.md)
