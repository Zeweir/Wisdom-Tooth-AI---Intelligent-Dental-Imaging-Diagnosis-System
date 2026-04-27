# Wisdom Tooth AI - Intelligent Dental Imaging Diagnosis System

基于 `docs/dev.md` 落地的一版最小可运行 MVP，包含：

 
 - `backend`：FastAPI 接口服务
 - `frontend`：Vue 3 + TypeScript + Vite 医生工作台

 
当前 MVP 聚焦文档中的主链路：

 
 - 影像上传
 - AI 分析结果查询
 - 报告医生审核
 - WebSocket 分析事件演示
 - PostgreSQL 持久化存储
 - MinIO 文件存储
 - Logto 登录、JWT 鉴权与角色权限控制

## 目录结构

```text
backend/
  app/main.py
  app/models.py
  app/database.py
  alembic/
  alembic.ini
  requirements.txt
  Dockerfile
frontend/
  src/App.vue
  src/api/
  src/types/
  src/components/
  package.json
  Dockerfile
  nginx.conf
docker-compose.yml
docs/
  dev.md
```

## 本地开发启动

### 1. 启动 PostgreSQL

你可以使用本机 PostgreSQL，也可以只启动数据库容器：

```bash
docker compose up -d postgres
```

默认数据库连接串见 `.env.example`：

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/wisdom_tooth_ai
```

### 2. 启动后端

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

建议在 `backend` 目录下执行 `uvicorn`。

### 3. 启动前端

```bash
npm install
npm run dev
```

建议在 `frontend` 目录下执行前端命令。

如需直连本地后端，可在 `frontend/.env` 中配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_LOGTO_ENDPOINT=http://127.0.0.1:3001
VITE_LOGTO_APP_ID=replace-with-your-logto-spa-app-id
VITE_LOGTO_API_RESOURCE=https://api.wisdom-tooth-ai.local
```

### 4. 初始化 Logto

启动自托管 Logto 后，打开：

- 管理台：`http://127.0.0.1:3002`
- OIDC 端点：`http://127.0.0.1:3001`

请在 Logto Console 中完成以下配置：

- 创建一个 **SPA Application**
- Redirect URI 填：`http://127.0.0.1:5173/callback`
- Post sign-out redirect URI 填：`http://127.0.0.1:5173/`
- 创建 API Resource：`https://api.wisdom-tooth-ai.local`
- 创建 scopes：`read:images`、`upload:images`、`review:reports`、`finalize:reports`
- 创建角色并分配 scopes，例如：
  - `radiologist`：`read:images`、`upload:images`
  - `doctor`：`read:images`、`review:reports`
  - `chief_doctor`：`read:images`、`review:reports`、`finalize:reports`

然后把 SPA 的 App ID 填入前端环境变量 `VITE_LOGTO_APP_ID`。

## Docker Compose 一键启动

```bash
docker compose up --build
```

启动后访问：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- 数据库：`localhost:5432`
- MinIO API：`http://127.0.0.1:9000`
- MinIO Console：`http://127.0.0.1:9001`
- Logto：`http://127.0.0.1:3001`
- Logto Admin：`http://127.0.0.1:3002`

默认访问地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- 接口文档：`http://127.0.0.1:8000/docs`

## 已实现接口

- `GET /api/v1/auth/me`
- `GET /api/v1/auth/rbac-model`
- `POST /api/v1/images/upload`
- `GET /api/v1/images`
- `GET /api/v1/analysis/{image_id}`
- `GET /api/v1/images/{image_id}/file`
- `PUT /api/v1/reports/{report_id}/review`
- `WS /ws/analysis/{image_id}`

## 当前实现说明

当前版本已经完成以下工程化增强：

- 后端已切换为 `PostgreSQL + SQLAlchemy` 持久化
- 已引入 `Alembic` 管理数据库迁移
- 上传文件已支持通过 `MinIO` 存储
- AI 检测结果与报告内容为模拟生成
- 前端已拆分为 `api / types / components` 结构
- 分析详情支持基础影像预览
- 已接入 `Logto OSS` 提供登录、JWT 校验与 RBAC
- 前端已支持显示当前角色、权限菜单显隐与无权限提示页
- 后端已提供当前访问画像与 RBAC 模型说明接口
- 提供 `docker-compose.yml` 支持数据库、后端、前端一键启动
- 仍然不包含真实模型推理、对象存储、鉴权与任务队列

后续可以继续扩展：

- MinIO 文件存储
- Celery 异步分析任务
- Ollama / 本地 LLM 报告生成
- JWT + RBAC + 审计日志
