# 第五章：扩展与部署

## 5.1 本地开发环境搭建

### 前置条件

- Python 3.12+
- Node.js 18+
- Docker + Docker Compose V2
- DeepSeek API Key（或其他 LLM 的 Key）

### 后端启动

```bash
cd ai-interview-backend

# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动 PostgreSQL + Redis（Docker）
docker compose up -d postgres redis

# 4. 配置 .env
# 必须配置：
#   DEEPSEEK_API_KEY=your-key
#   POSTGRES_HOST=localhost
#   POSTGRES_PORT=5434
#   REDIS_HOST=localhost
#   REDIS_PORT=6382

# 5. 执行数据库迁移
alembic upgrade head

# 6. 创建管理员账号
python scripts/create_admin.py

# 7. 启动后端
python main.py
# 服务运行在 http://localhost:8006
# API 文档：http://localhost:8006/client (用户端)
#          http://localhost:8006/backoffice (管理端)
```

### 前端启动

```bash
cd ai-interview-frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
# 前端运行在 http://localhost:3000
# API 请求通过 Vite proxy 转发到后端
```

## 5.2 Docker 部署

### 生产环境部署

```bash
cd ai-interview-backend

# 1. 配置 .env（参考部署文档）
# 关键配置：
#   ENV=production
#   SECRET_KEY=随机长字符串
#   DEEPSEEK_API_KEY=your-key
#   POSTGRES_PASSWORD=强密码

# 2. 启动所有服务
docker compose up -d

# 3. 执行数据库迁移
docker compose exec app alembic upgrade head

# 4. 创建管理员
docker compose exec app python scripts/create_admin.py

# 5. 检查健康状态
curl http://localhost:8006/api/v1/config/health
```

### Docker Compose 服务编排

```yaml
services:
  app:              # FastAPI 应用
  celery-worker:    # Celery 异步任务
  celery-beat:      # Celery 定时任务
  postgres:         # PostgreSQL 数据库
  redis:            # Redis 缓存
  nginx:            # 反向代理
  flower:           # Celery 监控（可选）
```

### 多环境配置

| 文件 | 用途 |
|------|------|
| `docker-compose.yml` | 基础配置 |
| `docker-compose.dev.yml` | 开发覆盖（热重载、宿主网络） |
| `docker-compose.prod.yml` | 生产覆盖（预构建镜像、日志限制） |

```bash
# 开发环境
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 生产环境
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 5.3 CI/CD 流水线

项目配置了 3 个 GitHub Actions 工作流：

### `quick-check.yml` — PR 质量检查

触发条件：PR 到 dev/preview/main/production 分支

检查项：
- Python 语法检查
- flake8 关键错误
- Black/isort 格式（警告）
- Docker 语法验证
- Bandit 安全扫描

### `preview-deploy.yml` — 预览环境部署

触发条件：push 到 `preview` 分支

流程：
1. 运行测试套件
2. 构建 Docker 镜像并推送到 GHCR
3. SSH 部署到预览服务器
4. 执行数据库迁移
5. 健康检查验证

### `production-deploy.yml` — 生产环境部署

触发条件：push 到 `main`/`production` 分支

流程：
1. 数据库备份
2. 安全扫描（Bandit + Safety）
3. 构建并推送镜像
4. SSH 部署 + 迁移
5. 健康检查
6. 失败自动回滚

## 5.4 已内置的扩展功能

以下功能代码已存在但默认未启用，按需开启：

### 邮件验证

启用邮箱注册验证功能：

```env
# .env
MAIL_ENABLED=true
MAIL_HOST=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password
```

配合 Celery Worker 发送异步邮件。

### 密码重置

依赖邮件功能，启用后用户可通过邮箱重置密码。

### 等待列表

当系统未完全开放注册时，用户可加入等待列表（`waiting_list` 表）。

### AWS S3 文件存储

将简历文件存储到 S3 而非本地磁盘：

```env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_BUCKET_NAME=your-bucket
AWS_REGION=us-east-1
```

### Nginx 反向代理

生产环境建议启用 Nginx：
- SSL/TLS 终止
- 静态文件服务
- 请求限流
- 负载均衡

配置文件在 `nginx/nginx.conf`。

### Flower 监控

Celery 任务监控面板：

```bash
docker compose --profile monitoring up -d
# 访问 http://localhost:5555
```

### RAG 知识库

基于 pgvector 的知识库检索增强：

1. 上传文档到知识库（管理后台 → 知识库管理）
2. 文档自动分块并生成向量嵌入
3. 面试时可检索相关知识辅助出题

### 题库管理

管理员可维护题库，支持：
- 手动添加题目
- 按分类/难度管理
- 向量语义搜索

## 5.5 检索测试功能详解

系统提供两套独立的检索测试入口，分别用于验证知识文档和题库的向量检索效果。两者共享同一套 Embedding + pgvector 基础设施，但搜索目标、过滤维度和返回结构不同。

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (Vue 3)                         │
│                                                         │
│  DocumentManagement.vue        QuestionBank.vue         │
│  ┌───────────────────┐        ┌───────────────────┐    │
│  │ 检索测试 Modal     │        │ 检索测试 Panel     │    │
│  │ • query           │        │ • query           │    │
│  │ • top_k           │        │ • top_k           │    │
│  │ • category        │        │ • position_tag    │    │
│  │                   │        │ • difficulty      │    │
│  │                   │        │ • min_score       │    │
│  └────────┬──────────┘        └────────┬──────────┘    │
│           │                            │                │
│           ▼                            ▼                │
│  knowledgeApi             questionBankApi               │
│  .testRetrieve()          .testRetrieve()               │
└───────────┬────────────────────────────┬────────────────┘
            │ POST                       │ POST
            ▼                            ▼
┌─────────────────────────────────────────────────────────┐
│                   后端 (FastAPI)                         │
│                                                         │
│  /knowledge/test-retrieve    /question-bank/test-retrieve│
│            │                            │                │
│            ▼                            ▼                │
│  knowledge_service         question_bank_service        │
│  .test_retrieve()          .test_retrieve()             │
│            │                            │                │
│            └──────────┬─────────────────┘                │
│                       ▼                                 │
│              embedding_service                          │
│  ┌─────────────────────────────────────────┐            │
│  │ 1. get_embedding(query) → float[1024]   │            │
│  │ 2. vector_search(model, filters, top_k) │            │
│  │    SQL: 1 - (embedding <=> query_vec)   │            │
│  └─────────────────────────────────────────┘            │
│                       │                                 │
│                       ▼                                 │
│              PostgreSQL + pgvector                      │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ knowledge_chunks │  │ question_banks   │            │
│  │ embedding Vector │  │ embedding Vector │            │
│  │   (1024)         │  │   (1024)         │            │
│  └──────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### 知识文档检索测试

**入口：** 管理后台 → 知识库管理 → 页面顶部「检索测试」按钮

**前端组件：** [DocumentManagement.vue](ai-interview-frontend/src/views/admin/DocumentManagement.vue)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| query | string | 必填 | 搜索查询文本 |
| top_k | int | 5 | 返回最大结果数 |
| category | string | 可选 | 按文档分类过滤 |

**后端流程：**

1. **生成查询向量** — 调用 `embedding_service.get_embedding(query)`，通过 OpenAI 兼容 API 生成 1024 维向量
2. **构建过滤条件** — 仅搜索已向量化（`is_vectorized=True`）且所属文档已启用的 chunk；如有 category 参数，进一步限定文档分类
3. **向量检索** — pgvector 余弦相似度搜索，按相似度降序取 top_k 条
4. **组装结果** — 加载父文档标题，返回 similarity_score、chunk_content、document_title、chunk_index

**响应示例：**

```json
{
  "code": 200,
  "data": [
    {
      "similarity_score": 0.8732,
      "chunk_content": "Spring Boot 自动配置原理...",
      "document_id": 12,
      "document_title": "Java后端面试题集",
      "chunk_index": 5
    }
  ]
}
```

### 题库检索测试

**入口：** 管理后台 → 题库管理 → 操作栏「检索测试」按钮

**前端组件：** [QuestionBank.vue](ai-interview-frontend/src/views/admin/QuestionBank.vue)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| query | string | 必填 | 搜索查询文本 |
| top_k | int | 5 | 返回最大结果数 |
| position_tag | string | 可选 | 按岗位标签过滤 |
| difficulty | string | 可选 | easy / medium / hard |
| min_score | float | 可选 | 最低相似度阈值 |

**后端流程：**

1. **生成查询向量** — 同上
2. **构建过滤条件** — 仅搜索启用的题目（`is_enabled=True`），可叠加 position_tag、difficulty 过滤
3. **向量检索** — 支持 min_score 阈值过滤，低于阈值的结果被丢弃
4. **组装结果** — 返回 similarity_score、question、category、difficulty、position_tag、reference_answer

**响应示例：**

```json
{
  "code": 200,
  "data": [
    {
      "similarity_score": 0.9124,
      "question_id": 45,
      "question": "请解释 Redis 缓存穿透的解决方案",
      "category": "Redis",
      "difficulty": "medium",
      "position_tag": "后端开发",
      "reference_answer": "缓存穿透是指查询一个一定不存在的数据..."
    }
  ]
}
```

### 核心服务：EmbeddingService

**文件：** [embedding_service.py](ai-interview-backend/app/services/embedding_service.py)

两个关键方法：

```python
# 生成文本向量
async def get_embedding(text: str) -> Optional[List[float]]:
    # 使用 OpenAI 兼容客户端
    # 默认模型: text-embedding-3-small, 维度: 1024
    # 可通过 LLMProvider/LLMModel 表或环境变量配置

# 向量检索
async def vector_search(db, model_class, query_embedding, filters, top_k, min_score=None):
    # SQL: SELECT *, (1 - embedding <=> query_vec) AS similarity_score
    #      FROM {table}
    #      WHERE {filters}
    #      ORDER BY embedding <=> query_vec
    #      LIMIT {top_k}
    # pgvector 余弦距离算子: <=>
```

### 数据模型

**知识文档分块** — [knowledge_document.py](ai-interview-backend/app/models/knowledge_document.py)

| 字段 | 类型 | 说明 |
|------|------|------|
| document_id | FK → knowledge_documents | 所属文档 |
| chunk_index | int | 分块序号 |
| content | text | 分块文本内容 |
| is_vectorized | bool | 是否已生成向量 |
| embedding | Vector(1024) | pgvector 向量 |

**题库** — [question_bank.py](ai-interview-backend/app/models/question_bank.py)

| 字段 | 类型 | 说明 |
|------|------|------|
| category | str | 题目分类 |
| position_tag | str | 岗位标签 |
| difficulty | str | easy/medium/hard |
| question | text | 题目内容 |
| reference_answer | text | 参考答案 |
| key_points | JSONB | 关键得分点 |
| is_vectorized | bool | 是否已生成向量 |
| embedding | Vector(1024) | pgvector 向量 |

### 两套测试的差异对比

| 维度 | 知识文档测试 | 题库测试 |
|------|-------------|---------|
| API 路径 | `/knowledge/test-retrieve` | `/question-bank/test-retrieve` |
| 搜索目标 | KnowledgeChunk（文档片段） | QuestionBank（完整题目） |
| 过滤参数 | category | position_tag, difficulty, min_score |
| 返回内容 | chunk_content, document_title, chunk_index | question, category, difficulty, reference_answer |
| 分数显示 | 4 位小数（toFixed(4)） | 百分比（×100, toFixed(1)） |
| 前端页面 | /admin/documents | /admin/question-bank |
| 模态框 | 标准 Modal | 大号 Modal（admin-modal-lg） |

### 岗位模板

预设不同岗位的面试配置：
- 推荐难度
- 推荐题目数
- 评估维度权重

## 5.6 常见问题排查

### 后端启动失败

```bash
# 查看日志
docker compose logs app

# 常见原因：
# 1. 数据库未就绪 → 等待 PostgreSQL health check 通过
# 2. 端口冲突 → 检查 8006/5434/6382 是否被占用
# 3. .env 配置错误 → 检查数据库连接信息
```

### AI 请求超时

```bash
# 检查 DeepSeek API Key 是否有效
curl https://api.deepseek.com/v1/models -H "Authorization: Bearer YOUR_KEY"

# 如果使用代理
USE_HTTP_PROXY=true
HTTP_PROXY=http://127.0.0.1:7890
```

### 前端无法连接后端

1. 确认后端运行中：`curl http://localhost:8006/api/v1/config/health`
2. 检查 `vite.config.js` 中的 proxy 目标地址
3. 如果后端在远程服务器，修改 target 为服务器 IP

### 数据库重置

```bash
# 删除所有数据重新开始
docker compose down -v  # -v 删除数据卷
docker compose up -d postgres redis
docker compose exec app alembic upgrade head
docker compose exec app python scripts/create_admin.py
```

## 5.7 生产环境建议

### 安全清单

- [ ] 修改 `SECRET_KEY` 为随机长字符串
- [ ] 修改默认数据库密码
- [ ] 启用 HTTPS（Nginx + SSL 证书）
- [ ] 限制 CORS 来源（非 `"*"`）
- [ ] 定期轮换 API Key
- [ ] 启用邮件验证（防垃圾注册）

### 性能优化

- [ ] 启用 Redis 缓存（已内置）
- [ ] 配置 Nginx 静态文件缓存
- [ ] 数据库连接池调优
- [ ] Celery Worker 并发数调整
- [ ] 前端构建优化（`npm run build`）

### 监控

- Flower 监控 Celery 任务
- PostgreSQL 慢查询日志
- 应用日志集中收集
- Docker 容器资源监控

## 5.8 扩展开发指南

### 新增 API 接口

1. 在 `app/api/client/v1/` 或 `app/api/backoffice/v1/` 下创建新文件：

```python
# app/api/client/v1/new_feature.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/hello")
async def hello():
    return {"message": "Hello"}
```

2. 在 `route/router_registry.py` 中注册：

```python
CLIENT_ROUTES = [
    # ... 现有路由
    RouteConfig("app.api.client.v1.new_feature", "/api/v1/new-feature", ["new-feature"]),
]
```

### 新增数据库模型

1. 在 `app/models/` 下创建模型文件
2. 在 `app/models/__init__.py` 中导入
3. 生成迁移：`alembic revision --autogenerate -m "add_new_table"`
4. 执行迁移：`alembic upgrade head`

### 切换 LLM 提供商

无需改代码，通过管理后台操作：

1. 登录管理后台 → LLM 配置
2. 添加新 Provider（填写 Base URL 和 API Key）
3. 添加新 Model（关联 Provider，填写模型名称）
4. 设置为激活状态

支持任何 OpenAI 兼容的 API（GPT-4、Claude、通义千问等）。

---

> **上一章**：[04-核心流程](../04-核心流程/README.md)
>
> **下一章**：[06-宝塔面板部署](../06-宝塔面板部署/README.md)
