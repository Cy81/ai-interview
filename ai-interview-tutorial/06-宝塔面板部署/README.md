# 第六章：宝塔面板快速部署

本章介绍如何通过宝塔面板在 Linux 服务器上快速部署 AI-Interview 项目。

## 6.1 环境要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | CentOS 7+ / Ubuntu 18.04+ | Ubuntu 22.04 LTS |
| 内存 | 2GB | 4GB+ |
| 磁盘 | 20GB | 50GB+ SSD |
| 宝塔面板 | 9.0+ | 最新版 |
| Docker | 20.10+ | 最新版 |
| Docker Compose | V2 | 最新版 |

### 安装 Docker（通过宝塔面板）

1. 登录宝塔面板 → **软件商店** → 搜索 **Docker**
2. 点击 **安装** → 选择 **Docker管理器**
3. 安装完成后，在左侧菜单找到 **Docker** 进入管理界面

> 如果面板没有 Docker 一键安装，可通过 SSH 执行：
> ```bash
> curl -fsSL https://get.docker.com | bash
> systemctl enable docker && systemctl start docker
> ```

### 安装 Docker Compose

```bash
# 下载 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
chmod +x /usr/local/bin/docker-compose

# 验证
docker-compose --version
```

## 6.2 获取代码

通过宝塔面板 **终端** 或 SSH 登录服务器执行：

```bash
# 进入网站根目录（按需修改）
cd /www/wwwroot

# 克隆项目
git clone https://github.com/Cy81/ai-interview.git

# 进入后端目录
cd ai-interview/ai-interview-backend
```

## 6.3 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

### 必须修改的配置

```env
# ===== 基础配置 =====
ENV=production
SECRET_KEY=你的随机密钥字符串-越长越好-至少32位
API_PORT=8006

# ===== 数据库配置 =====
POSTGRES_USER=ai_interview          # 数据库用户名
POSTGRES_PASSWORD=你的强密码          # 数据库密码
POSTGRES_HOST=localhost
POSTGRES_PORT=5434
POSTGRES_DB=ai_interview            # 数据库名

# ===== Redis 配置 =====
REDIS_HOST=localhost
REDIS_PORT=6382
REDIS_PASSWORD=你的Redis密码

# ===== AI 配置（必填） =====
DEEPSEEK_API_KEY=你的DeepSeek-API-Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 生成 SECRET_KEY

```bash
# 随机生成一个 64 位密钥
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 获取 DeepSeek API Key

1. 访问 https://platform.deepseek.com/
2. 注册并登录
3. 进入 **API Keys** → **创建 API Key**
4. 复制 Key 填入 `.env` 的 `DEEPSEEK_API_KEY`

## 6.4 启动服务

### 方式一：宝塔终端执行（推荐）

```bash
cd /www/wwwroot/ai-interview/ai-interview-backend

# 构建并启动所有服务
docker-compose up -d --build

# 查看运行状态
docker-compose ps

# 查看日志（排查问题时使用）
docker-compose logs -f app
```

### 方式二：宝塔 Docker 管理器

1. 宝塔面板 → **Docker** → **编排**
2. 点击 **创建编排**
3. 名称填写 `ai-interview`
4. 将 `docker-compose.yml` 内容粘贴进去
5. 在 **环境变量** 中导入 `.env` 的内容
6. 点击 **构建并启动**

### 启动后的服务列表

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| app | ai-interview-app | 8006 | FastAPI 应用 |
| postgres | ai-interview-postgres | 5434→5432 | PostgreSQL 数据库 |
| redis | ai-interview-redis | 6382→6379 | Redis 缓存 |
| celery-worker | ai-interview-celery-worker | — | 异步任务处理 |
| celery-beat | ai-interview-celery-beat | — | 定时任务调度 |
| nginx | ai-interview-nginx | 8080→80 | Nginx 反向代理 |

### 验证服务健康

```bash
# 检查所有容器状态
docker-compose ps

# 检查应用健康接口
curl http://localhost:8006/api/v1/config/health

# 预期返回
# {"code": 200, "message": "Success", "data": {"status": "healthy"}}
```

## 6.5 初始化数据库

```bash
# 进入应用容器
docker-compose exec app bash

# 执行数据库迁移
alembic upgrade head

# 创建超级管理员
python scripts/create_first_admin.py

# 退出容器
exit
```

### 默认管理员账号

| 字段 | 值 |
|------|-----|
| 邮箱 | admin@ai-interview.com |
| 密码 | ai-interview&admin |
| 角色 | superadmin |

> **安全提示：** 首次登录后请立即修改管理员密码。

## 6.6 配置 Nginx 反向代理

### 方式一：宝塔面板可视化配置（推荐）

1. 宝塔面板 → **网站** → **添加站点**
   - 域名：填写你的域名或服务器 IP
   - PHP 版本：选择 **纯静态**
   - 备注：ai-interview

2. 点击站点名称 → **反向代理** → **添加反向代理**
   - 代理名称：`ai-api`
   - 目标 URL：`http://127.0.0.1:8006`
   - 发送域名：`$host`

3. 如果前后端分开部署，再添加前端代理：
   - 代理名称：`ai-frontend`
   - 目标 URL：`http://127.0.0.1:3000`（前端开发服务器端口）
   - 发送域名：$host

4. 如需部署前端生产版本，使用 Nginx 静态托管：
   ```bash
   # 在服务器上构建前端
   cd /www/wwwroot/ai-interview/ai-interview-frontend
   npm install && npm run build
   
   # 将 dist 目录指向站点根目录
   # 宝塔面板 → 站点 → 设置 → 目录 → /www/wwwroot/ai-interview/ai-interview-frontend/dist
   ```

### 方式二：手动编写 Nginx 配置

宝塔面板 → **网站** → 点击站点名 → **配置文件**，粘贴：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或 IP

    # SSL 配置（申请证书后取消注释）
    # listen 443 ssl;
    # ssl_certificate    /www/server/panel/vhost/cert/your-domain.com/fullchain.pem;
    # ssl_certificate_key /www/server/panel/vhost/cert/your-domain.com/privkey.pem;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # 前端静态文件
    location / {
        root /www/wwwroot/ai-interview/ai-interview-frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 管理后台 API（如需单独路径）
    location /backoffice/ {
        proxy_pass http://127.0.0.1:8006/backoffice/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 6.7 配置 SSL 证书

1. 宝塔面板 → **网站** → 点击站点名 → **SSL**
2. 选择 **Let's Encrypt** → 勾选域名 → **申请**
3. 申请成功后开启 **强制 HTTPS**

> **前提：** 域名已解析到服务器 IP，且 80 端口可正常访问。

## 6.8 防火墙放行端口

宝塔面板 → **安全** → **系统防火墙** → 放行以下端口：

| 端口 | 用途 | 协议 |
|------|------|------|
| 80 | HTTP | TCP |
| 443 | HTTPS | TCP |
| 8006 | 后端 API（可选，仅调试用） | TCP |

> 生产环境建议只开放 80/443，API 通过 Nginx 代理访问。

## 6.9 部署验证

### 检查清单

```bash
# 1. 所有容器运行正常
docker-compose ps
# 预期：所有服务状态为 running/healthy

# 2. 应用健康检查
curl http://localhost:8006/api/v1/config/health

# 3. API 文档可访问
# 用户端：http://your-domain.com/client/
# 管理端：http://your-domain.com/backoffice/

# 4. 前端可访问
# http://your-domain.com/
```

### 功能验证

1. **用户注册** → 访问前端 → 点击注册 → 填写信息 → 注册成功
2. **管理员登录** → 访问 `/admin/login` → 使用默认账号登录
3. **上传简历** → 登录后 → 上传简历 → 选择岗位模板 → 开始面试
4. **LLM 配置** → 管理后台 → LLM 配置 → 确认 DeepSeek 模型已激活

## 6.10 常用运维命令

### 服务管理

```bash
cd /www/wwwroot/ai-interview/ai-interview-backend

# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启指定服务
docker-compose restart app

# 查看日志
docker-compose logs -f app          # 应用日志
docker-compose logs -f celery-worker # 异步任务日志

# 查看资源占用
docker stats
```

### 更新部署

```bash
cd /www/wwwroot/ai-interview/ai-interview-backend

# 拉取最新代码
git pull origin master

# 重新构建并启动
docker-compose up -d --build

# 执行数据库迁移（如有）
docker-compose exec app alembic upgrade head
```

### 数据库备份

```bash
# 通过 Docker 备份 PostgreSQL
docker-compose exec postgres pg_dump -U ai_interview ai_interview > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker-compose exec postgres psql -U ai_interview ai_interview < backup_20260619.sql
```

> 也可通过宝塔面板 → **数据库** → **备份** 进行可视化操作。

### 查看容器日志排查问题

```bash
# 查看应用启动日志
docker-compose logs --tail=100 app

# 查看数据库连接问题
docker-compose logs --tail=50 postgres

# 进入容器调试
docker-compose exec app bash
```

## 6.11 常见问题

### 容器启动失败

```bash
# 查看详细错误
docker-compose logs app

# 常见原因：
# 1. .env 配置错误 → 检查数据库密码、API Key
# 2. 端口被占用 → lsof -i:8006 或 lsof -i:5434
# 3. 数据库未就绪 → 等待 postgres 健康检查通过
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
docker-compose ps postgres

# 测试连接
docker-compose exec postgres psql -U ai_interview -d ai_interview -c "SELECT 1;"

# 如果密码错误，重新初始化
docker-compose down -v  # -v 删除数据卷！
# 修改 .env 中的密码后重新启动
docker-compose up -d postgres redis
docker-compose exec app alembic upgrade head
```

### API 请求超时

```bash
# 检查 DeepSeek API Key 是否有效
curl https://api.deepseek.com/v1/models -H "Authorization: Bearer YOUR_KEY"

# 如果服务器在大陆，可能需要代理
# 在 .env 中配置：
USE_HTTP_PROXY=true
HTTP_PROXY=http://127.0.0.1:7890
```

### 前端无法访问

1. 确认 Nginx 反向代理配置正确
2. 检查宝塔面板站点是否正常运行
3. 检查防火墙是否放行 80/443 端口
4. 如果使用 CDN，确认回源地址正确

### 磁盘空间不足

```bash
# 清理 Docker 无用资源
docker system prune -a

# 清理日志
docker-compose logs --tail=0 app  # 截断日志

# 查看磁盘占用
du -sh /www/wwwroot/ai-interview/*
```

## 6.12 安全加固

部署完成后，建议执行以下安全措施：

- [ ] 修改 `.env` 中的 `SECRET_KEY` 为随机强密钥
- [ ] 修改 `.env` 中的数据库密码和 Redis 密码
- [ ] 修改默认管理员密码（登录后在个人中心修改）
- [ ] 宝塔面板开启 **面板安全设置**（修改端口、开启二次验证）
- [ ] 配置 SSL 证书并开启强制 HTTPS
- [ ] 关闭不必要的端口（仅保留 80、443）
- [ ] 定期备份数据库（建议每天自动备份）
- [ ] 开启宝塔防火墙，限制 SSH 登录 IP

---

> **上一章**：[05-扩展与部署](../05-扩展与部署/README.md)
