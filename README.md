# Wisdom Tooth AI - Intelligent Dental Imaging Diagnosis System

基于 `docs/dev.md` 落地的一版最小可运行 MVP，包含：

 
 - `backend`：FastAPI 接口服务
 - `frontend`：Vue 3 + TypeScript + Vite 医生工作台

 
当前 MVP 聚焦文档中的主链路：


- 影像上传
- 患者档案与病例归档
- 公开牙科影像数据集登记
- AI 分析结果查询
- 报告医生审核
- 患者历史报告预览与工作站病例深链接
- 报告版本历史与归档追踪
- WebSocket 分析事件演示
- PostgreSQL 持久化存储
- MinIO 文件存储
- Logto 登录、JWT 鉴权与角色权限控制
- Celery + Redis 后台分析任务
- 可选 YOLOv8 本地权重推理（失败时自动回退到 Ollama / mock）
- 本地 Ollama 多模态报告生成（失败时自动回退到内置 mock）

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

上面这段是本地开发示例。Docker 部署参数请使用根目录 `.env`，服务器部署步骤见 [docs/deploy.md](C:/Projects/Wisdom-Tooth-AI---Intelligent-Dental-Imaging-Diagnosis-System/docs/deploy.md)。

本地 Ollama 示例配置：

```env
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://10.41.33.17:11434
OLLAMA_MODEL=qwen3.5:9b
OLLAMA_TIMEOUT_SECONDS=120
```

如需启用真实 YOLO 牙片检测，请将权重文件放在仓库外或本地 `models/` 目录，并配置：

```env
YOLO_ENABLED=true
YOLO_MODEL_PATH=C:\models\dental-yolo.pt
YOLO_CONF_THRESHOLD=0.25
YOLO_IMAGE_SIZE=1024
YOLO_DEVICE=
YOLO_CLASS_MAP_JSON=
```

`YOLO_MODEL_PATH` 为空或文件不存在时，系统会自动跳过 YOLO，继续使用 Ollama / mock 分析。Docker Compose 默认把 `./models` 挂载到容器 `/models`，可将权重放到 `models/dental-yolo.pt`。

如需从 Kaggle 下载公开牙科数据集，先配置本机环境变量，下载脚本会优先读取 `KAGGLE_USERNAME` / `KAGGLE_KEY`，Windows 下也会 fallback 到用户环境变量注册表：

```powershell
setx KAGGLE_USERNAME "your-kaggle-username"
setx KAGGLE_KEY "your-kaggle-api-key"
python scripts/download_dataset.py --extract --extract-dir datasets/x
```

也可以下载指定 Kaggle slug：

```powershell
python scripts/download_dataset.py --kaggle ermecan/dental-x-ray-dataset --filename dental-x-ray-dataset.zip --extract --extract-dir datasets/dental_xray
```

Docker Compose 会把本机 `./datasets` 只读挂载到后端和 Worker 容器的 `/datasets`。在“数据集中心”新建导入时选择“本地目录登记”，可填写例如 `/datasets/x`、`/datasets/dental_xray`、`/datasets/panoramic_disease`，后端会扫描目录并生成样本索引。

### 2. 启动后端

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

建议在 `backend` 目录下执行 `uvicorn`。

如果你要使用正式异步分析任务，还需要再开一个终端启动 Worker：

```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

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

推荐先复制根目录环境变量模板：

```bash
cp .env.example .env
```

服务器部署时，至少把 `.env` 里的 `PUBLIC_HOST` 改成你的公网 IP，并在 Logto 中创建 SPA 应用后填好 `VITE_LOGTO_APP_ID`。完整步骤见 [docs/deploy.md](C:/Projects/Wisdom-Tooth-AI---Intelligent-Dental-Imaging-Diagnosis-System/docs/deploy.md)。

```bash
docker compose up --build
```

Docker 前端构建会读取根目录 `.env` 里的 `VITE_*` 变量，尤其是 `VITE_LOGTO_APP_ID`。如需统一走前端 nginx 代理，请将 `VITE_API_BASE_URL` 留空并重新构建前端镜像。

如果启用仓库内置的 `gateway` 反向代理，推荐对外只开放：

- `80`：跳转到 HTTPS
- `443`：前端与接口统一 HTTPS 入口
- `3001`：Logto OIDC
- `3002`：仅初始化期间临时开放的 Logto Admin

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
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/patients`
- `POST /api/v1/patients`
- `GET /api/v1/patients/{patient_id}`
- `PUT /api/v1/patients/{patient_id}`
- `GET /api/v1/patients/{patient_id}/images`
- `GET /api/v1/datasets`
- `POST /api/v1/datasets`
- `POST /api/v1/datasets/seed-public`
- `GET /api/v1/datasets/{dataset_id}`
- `PUT /api/v1/datasets/{dataset_id}`
- `GET /api/v1/datasets/{dataset_id}/imports`
- `POST /api/v1/datasets/{dataset_id}/imports`
- `POST /api/v1/datasets/{dataset_id}/imports/download-url`
- `POST /api/v1/dataset-imports/{import_id}/upload-zip`
- `GET /api/v1/dataset-imports/{import_id}/samples`
- `POST /api/v1/dataset-imports/{import_id}/split`
- `GET /api/v1/model-evaluations`
- `POST /api/v1/model-evaluations`
- `POST /api/v1/images/upload`
- `GET /api/v1/images`
- `GET /api/v1/analysis/{image_id}`
- `GET /api/v1/images/{image_id}/file`
- `PUT /api/v1/reports/{report_id}/review`
- `GET /api/v1/reports/{report_id}/revisions`
- `GET /api/v1/audit-logs`
- `WS /ws/analysis/{image_id}`

## 当前实现说明

当前版本已经完成以下工程化增强：

- 后端已切换为 `PostgreSQL + SQLAlchemy` 持久化
- 已引入 `Alembic` 管理数据库迁移
- 上传文件已支持通过 `MinIO` 存储
- AI 分析任务已切换为 `Celery + Redis`
- 已支持优先调用本地 `YOLO` 权重进行检测，未配置或失败时回退到 `Ollama` / mock
- 已支持优先调用本地 `Ollama` 多模态模型生成检测结果与中文报告
- 当 Ollama 不可达或返回异常时，会自动回退到内置 mock 分析结果
- 前端已拆分为 `api / types / components` 结构
- 分析详情支持基础影像预览
- 已接入 `Logto OSS` 提供登录、JWT 校验与 RBAC
- 前端已支持显示当前角色、权限菜单显隐与无权限提示页
- 后端已提供当前访问画像与 RBAC 模型说明接口
- 已支持优先读取 token 中的角色 claim，并在缺失时回退到基于 scope 的角色推断
- 权限说明区域已包含角色来源、claim 摘要与菜单映射调试信息
- 已提供审计日志表与关键动作留痕
- 已支持影像列表、审计日志分页查询与工作台摘要统计
- 已支持患者档案、患者搜索、病例时间线和上传时自动建档
- 已支持公开数据集登记、seed 初始化、筛选、公开 zip 直链下载和数据准备指标
- 已支持数据集导入批次、样本索引、训练集划分和模型评估记录
- 前端已支持报告 HTML 导出、浏览器打印预览和影像检测框叠加展示
- 前端已支持 `/workspace?image_id=<id>` 深链接，可从首页和患者病例时间线直接打开指定病例
- 患者档案已支持历史病例报告预览、医生意见摘要和归档状态查看
- 报告审核与正式确认会自动生成报告版本快照，支持在工作站和患者档案查看版本历史
- 审计中心已支持报告审核、正式确认、数据导入、患者更新等常用快捷筛选
- 提供 `docker-compose.yml` 支持数据库、后端、前端一键启动

后续可以继续扩展：

- 更精细的影像检测模型与分割结果可视化
- 数据集标注格式转换、质量校验与真实训练任务编排
- 患者端/多租户角色扩展
- 更完整的审计查询与导出能力
- 更强的模型结果评估与人工复核流程

## 医生端闭环说明

- 首页最近病例和当前病例会跳转到 `/workspace?image_id=<id>`。
- 患者档案的历史病例同时提供“查看报告”和“打开病例”。
- 工作站会优先读取 URL 中的 `image_id` 并打开对应病例；如果没有指定，则沿用病例队列默认选择。
- 报告预览第一版复用现有分析记录中的 `report.content`、`doctor_review`、检测结果和更新时间，不额外生成 PDF。
- 报告版本历史通过 `GET /api/v1/reports/{report_id}/revisions` 读取；首次审核旧报告时会补一条 AI 草稿快照，之后每次审核或正式确认都会新增版本记录。
