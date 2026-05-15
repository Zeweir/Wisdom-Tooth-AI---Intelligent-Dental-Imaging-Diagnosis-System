# 智齿 AI — 牙齿影像智能诊断系统

基于 `docs/dev.md` 落地的最小可运行 MVP，包含：

- `backend`：FastAPI 接口服务
- `frontend`：Vue 3 + TypeScript + Vite 医生工作台

## 核心功能

- 影像上传与 AI 自动分析
- 患者档案与病例归档
- 公开牙科影像数据集登记
- AI 诊断结果可视化（检测框叠加、牙位总览）
- 报告审核与正式确认（版本快照）
- 工作台仪表盘（ECharts 图表统计）
- PostgreSQL 持久化存储
- MinIO 文件存储
- 自建登录系统（JWT + RBAC 三角色权限）
- Celery + Redis 后台分析任务
- 可选 YOLOv8 本地权重推理（失败回退 Ollama / mock）
- 可选 Ollama 多模态报告生成（失败回退内置 mock）
- 审计日志追踪

## 快速启动（Docker 一键部署）

```bash
git clone <repo-url> && cd Wisdom-Tooth-AI
cp .env.example .env
docker compose up -d --build
```

启动后访问：

| 服务 | 地址 |
|------|------|
| 前端 | `http://127.0.0.1:5173` |
| 后端 API | `http://127.0.0.1:8000` |
| API 文档 | `http://127.0.0.1:8000/docs` |
| MinIO Console | `http://127.0.0.1:9001` |

**默认账号：** `admin` / `admin123`（主任医生，全部权限）

系统首次启动会自动创建 3 个账号：

| 用户名 | 密码 | 角色 | 权限 |
|--------|------|------|------|
| `admin` | `admin123` | 主任医生 | 全部权限 |
| `doctor` | `doctor123` | 审核医生 | 查看影像、审核报告 |
| `tech` | `tech123` | 影像技师 | 查看影像、上传影像 |

## 公网部署（一键脚本）

```bash
chmod +x deploy/bootstrap-public-ip.sh
./deploy/bootstrap-public-ip.sh 你的公网IP
docker compose up -d --build
```

脚本会自动生成 `.env`、强密码和自签证书。部署后访问 `https://你的公网IP`。

## 本地开发

### 1. 启动基础服务

```bash
docker compose up -d postgres minio redis
```

### 2. 启动后端

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

可选：启动 Celery Worker 处理异步分析任务

```bash
cd backend
celery -A app.celery_app.celery_app worker --loglevel=info
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

如需直连本地后端，在 `frontend/.env.local` 中配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 4. 可选：启用 AI 模型

**Ollama 多模态报告：**

```env
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://10.41.33.17:11434
OLLAMA_MODEL=qwen3.5:9b
```

**YOLO 牙片检测：**

将权重文件放入 `models/` 目录，配置：

```env
YOLO_ENABLED=true
YOLO_MODEL_PATH=/models/dental-yolo.pt
YOLO_CONF_THRESHOLD=0.25
```

`YOLO_MODEL_PATH` 为空或文件不存在时，自动跳过 YOLO，回退到 Ollama / mock。

## 角色权限体系

| 角色 | 权限 |
|------|------|
| 影像技师 (`radiologist`) | 查看影像、上传影像 |
| 审核医生 (`doctor`) | 查看影像、审核报告 |
| 主任医生 (`chief_doctor`) | 全部权限（上传、查看、审核、正式确认） |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/auth/me` | 当前用户信息 |
| GET | `/api/v1/auth/rbac-model` | RBAC 模型 |
| GET | `/api/v1/dashboard/summary` | 仪表盘统计 |
| POST | `/api/v1/images/upload` | 上传影像 |
| GET | `/api/v1/images` | 影像列表 |
| GET | `/api/v1/analysis/{image_id}` | 分析详情 |
| GET | `/api/v1/images/{image_id}/file` | 影像文件 |
| PUT | `/api/v1/reports/{report_id}/review` | 审核报告 |
| GET | `/api/v1/reports/{report_id}/revisions` | 报告版本历史 |
| GET | `/api/v1/reports/{report_id}/pdf` | 下载 PDF 报告 |
| GET/POST/PUT | `/api/v1/patients` | 患者管理 |
| GET/POST/PUT | `/api/v1/datasets` | 数据集管理 |
| GET | `/api/v1/audit-logs` | 审计日志 |
| WS | `/ws/analysis/{image_id}` | 分析进度 |

完整接口文档：`http://127.0.0.1:8000/docs`

## 目录结构

```text
backend/
  app/main.py          # FastAPI 应用入口
  app/models.py        # SQLAlchemy 数据模型
  app/auth.py          # JWT 鉴权 + RBAC
  app/config.py        # 环境配置
  alembic/             # 数据库迁移
frontend/
  src/
    api/               # API 请求层
    components/        # Vue 组件
    composables/       # 组合式函数
    pages/             # 页面组件
    router/            # 路由配置
    types/             # TypeScript 类型
deploy/
  nginx/               # Nginx 网关配置
  bootstrap-public-ip.sh  # 公网部署脚本
docker-compose.yml
```

## CI/CD

每次 push 到 `main` 分支自动执行：

1. **自动版本号** — `vYYYY.MM.DD.N` 格式，当天第 N 次推送递增
2. **构建 Docker 镜像** — 前后端分别打包，推送至 `ghcr.io/<user>/wisdom-tooth-backend` 和 `ghcr.io/<user>/wisdom-tooth-frontend`
3. **打 Git Tag** — 自动推送版本号 tag
4. **创建 GitHub Release** — 附带自动生成的变更日志

PR 提交时执行 `ci.yml`：前端 TS 类型检查 + 构建，后端语法检查 + 鉴权单元测试。

### 服务器部署

服务器上只需安装 Docker，直接用 Actions 构建好的镜像：

```bash
# 1. 登录 GitHub Container Registry
echo "$GITHUB_TOKEN" | docker login ghcr.io -u 你的用户名 --password-stdin

# 2. 拉取镜像
docker pull ghcr.io/你的用户名/wisdom-tooth-backend:latest
docker pull ghcr.io/你的用户名/wisdom-tooth-frontend:latest

# 3. 使用 prod compose 启动（镜像不打本地构建）
cp .env.example .env
docker compose -f docker-compose.prod.yml up -d
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + TypeScript + Vite |
| UI 库 | Element Plus |
| 图表 | ECharts / vue-echarts |
| 后端框架 | FastAPI |
| ORM | SQLAlchemy 2.0 |
| 数据库 | PostgreSQL 16 |
| 迁移 | Alembic |
| 文件存储 | MinIO |
| 任务队列 | Celery + Redis |
| 鉴权 | JWT (HS256) + bcrypt |
| AI 推理 | YOLOv8 / Ollama |
| PDF 生成 | ReportLab |
| 反向代理 | Nginx |
| 容器化 | Docker Compose |
