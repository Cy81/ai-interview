# 第一章：项目概览

## 1.1 项目简介

**AI-Interview（智面）** 是一个基于 AI 的模拟面试平台。用户上传 PDF 简历后，系统通过 AI 解析简历结构、根据目标岗位生成面试题目、进行多轮对话式模拟面试（支持 SSE 实时流式反馈），最终生成包含评分、优劣势分析和录用建议的综合评估报告。

## 1.2 核心功能

| 功能模块 | 说明 |
|---------|------|
| 简历上传与解析 | 上传 PDF，AI 提取结构化信息并分析优劣势 |
| 智能出题 | 根据简历 + 目标岗位 + 难度生成定制面试题 |
| 多轮对话面试 | 支持普通/流式两种模式，AI 实时评估回答 |
| 综合评估报告 | 面试结束后生成包含各项评分的详细报告 |
| 管理后台 | 用户管理、面试管理、题库管理、知识库、LLM 配置等 |
| 动态 LLM 切换 | 管理员可在后台实时切换 AI 模型提供商 |

## 1.3 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12 | 主语言 |
| FastAPI | - | 异步 Web 框架 |
| SQLAlchemy 2.0 | async + asyncpg | ORM，异步数据库操作 |
| PostgreSQL | 16 | 主数据库（含 pgvector 向量扩展） |
| Redis | 7 | 缓存/消息队列 |
| Celery | Worker + Beat | 异步任务调度 |
| Alembic | - | 数据库迁移 |
| Docker | Compose V2 | 容器化部署 |
| OpenAI SDK | 1.82.0 | DeepSeek API 调用（OpenAI 兼容接口） |
| pdfplumber | - | PDF 文本提取 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4 | 前端框架 |
| Vite | 5.4 | 构建工具 |
| Vue Router | 4.3 | 路由管理 |
| Pinia | 2.1 | 状态管理 |
| Axios | 1.7 | HTTP 请求 |

## 1.4 项目目录结构

```
ai-interview/
├── ai-interview-backend/          # 后端服务
│   ├── app/
│   │   ├── api/                   # API 路由层
│   │   │   ├── client/v1/         #   用户端接口
│   │   │   └── backoffice/v1/     #   管理后台接口
│   │   ├── services/              # 业务逻辑层
│   │   │   ├── client/            #   用户端服务
│   │   │   ├── backoffice/        #   管理端服务
│   │   │   ├── common/            #   公共服务（Redis、邮件、线程池）
│   │   │   └── *.py               #   顶层服务（embedding、知识库、题库等）
│   │   ├── models/                # 数据库模型
│   │   ├── schemas/               # Pydantic 请求/响应 Schema
│   │   ├── route/                 # 应用工厂 + 路由注册中心
│   │   ├── core/                  # 配置、安全、日志、Celery
│   │   ├── db/                    # 数据库连接
│   │   ├── exceptions/            # 自定义异常
│   │   └── schedule/              # Celery 定时任务
│   ├── main.py                    # 入口文件
│   ├── docker-compose.yml         # 生产环境编排
│   ├── docker-compose.dev.yml     # 开发环境编排
│   ├── docker-compose.prod.yml    # 生产覆盖配置
│   ├── Dockerfile                 # 生产镜像
│   ├── Dockerfile.dev             # 开发镜像
│   ├── requirements.txt           # Python 依赖
│   └── alembic/                   # 数据库迁移
│
├── ai-interview-frontend/         # 用户前端（端口 3000）
│   ├── src/
│   │   ├── views/                 # 页面组件
│   │   │   ├── Login.vue          #   登录
│   │   │   ├── Register.vue       #   注册
│   │   │   ├── Dashboard.vue      #   仪表盘
│   │   │   ├── ResumeUpload.vue   #   简历上传
│   │   │   ├── Interview.vue      #   面试对话页
│   │   │   ├── Report.vue         #   评估报告
│   │   │   ├── Profile.vue        #   个人中心
│   │   │   └── admin/             #   管理后台页面
│   │   ├── api/                   # API 调用层
│   │   ├── stores/                # Pinia 状态管理
│   │   └── router/                # 路由配置
│   ├── vite.config.js
│   └── package.json
│
├── ai-interview-admin/            # 独立管理前端（端口 3001，备用）
├── ai-interview-tutorial/         # 本教程目录
│   ├── 01-项目概览/
│   ├── 02-后端详解/
│   ├── 03-前端详解/
│   ├── 04-核心流程/
│   └── 05-扩展与部署/
├── 部署文档.md
└── 本地运行.md
```

## 1.5 架构总览

```
┌─────────────────────────────────────────────────────┐
│                     用户浏览器                        │
│  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ 用户前端 (3000)   │  │ 管理后台 (前端内嵌 /admin) │  │
│  └────────┬─────────┘  └────────────┬─────────────┘  │
└───────────┼──────────────────────────┼───────────────┘
            │ HTTP / SSE              │ HTTP
            ▼                         ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI 后端 (8006)                      │
│                                                      │
│  ┌─────────────┐    ┌──────────────┐                 │
│  │ Client API  │    │ Backoffice   │                 │
│  │ /api/v1/... │    │ /api/v1/     │                 │
│  │ auth        │    │ backoffice/  │                 │
│  │ resumes     │    │ auth         │                 │
│  │ interviews  │    │ users        │                 │
│  └──────┬──────┘    │ interviews   │                 │
│         │           │ llm-config   │                 │
│         ▼           │ question-bank│                 │
│  ┌─────────────┐    │ knowledge    │                 │
│  │  Services   │◄───│ position-tpl │                 │
│  │ AIService   │    └──────────────┘                 │
│  │ InterviewSvc│                                    │
│  │ ResumeSvc   │    ┌──────────────┐                 │
│  └──────┬──────┘    │  Celery      │                 │
│         │           │ Worker+Beat  │                 │
└─────────┼───────────┴──────────────┼─────────────────┘
          │                          │
    ┌─────▼─────┐  ┌────────┐  ┌────▼────┐
    │ PostgreSQL │  │ Redis  │  │ DeepSeek│
    │  (5434)    │  │ (6382) │  │   API   │
    │  +pgvector │  └────────┘  └─────────┘
    └───────────┘
```

## 1.6 API 设计

项目采用 **双 API 架构**：

- **Client API** (`/api/v1/*`)：面向普通用户，包含认证、简历、面试等接口
- **Backoffice API** (`/api/v1/backoffice/*`)：面向管理员，包含用户管理、面试管理、LLM 配置等接口

两者共享同一个 Service 层，通过路由注册中心（`router_registry.py`）统一管理。

## 1.7 数据库表结构概览

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| users | 用户表 | email, hashed_password, first_name, last_name, avatar |
| admins | 管理员表 | email, hashed_password |
| resumes | 简历表 | user_id, file_url, parsed_content, analysis, status |
| interviews | 面试表 | user_id, resume_id, target_position, difficulty, status, questions_data |
| interview_messages | 面试消息 | interview_id, role, content, score |
| llm_providers | LLM 提供商 | name, base_url, is_active |
| llm_models | LLM 模型 | provider_id, model_name, is_active |
| knowledge_documents | 知识库文档 | title, content, file_url |
| knowledge_chunks | 文档分块 | document_id, content, embedding (vector) |
| question_banks | 题库 | question, answer, category, embedding |
| position_templates | 岗位模板 | position_name, difficulty, question_count |
| waiting_list | 等待列表 | email |

## 1.8 端口映射

| 服务 | 容器端口 | 宿主机端口 |
|------|---------|-----------|
| FastAPI | 8006 | 8006 |
| PostgreSQL | 5432 | 5434 |
| Redis | 6379 | 6382 |
| 用户前端 | - | 3000 |
| 管理前端 | - | 3001 |
| Nginx | 80 | 8080 |
| Flower (监控) | 5555 | 5555 |

---

> **下一章**：[02-后端详解](../02-后端详解/README.md)
