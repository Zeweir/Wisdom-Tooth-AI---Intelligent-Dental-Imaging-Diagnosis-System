# 项目启动文档

本文档说明如何在当前仓库中启动整个项目，包括：

- 本地开发启动
- Docker 一键启动
- 服务访问地址
- 常见问题排查

## 一、项目结构

当前项目包含以下模块：

- `backend`：FastAPI 后端服务
- `frontend`：Vue 3 + Vite 前端服务
- `postgres`：PostgreSQL 数据库（通过 Docker 启动）

## 二、环境准备

请先确认本机已安装以下软件：

- Python 3.13+
- Node.js 24+
- npm 11+
- Docker
- Docker Compose

## 三、本地开发启动

适合你边改代码边调试。

### 1. 启动数据库

在仓库根目录执行：

```bash
docker-compose up -d postgres
```

启动后，数据库默认配置如下：

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/wisdom_tooth_ai
```

如果你需要自定义环境变量，可以参考根目录下的 `.env.example`。

### 2. 启动后端

在仓库根目录执行：

```bash
python -m venv .venv
.venv\Scripts\activate
.venv\Scripts\python -m pip install -r backend\requirements.txt
```

建议先配置环境变量：

```env
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=wisdom-tooth-images
MINIO_SECURE=false
LOGTO_ENDPOINT=http://127.0.0.1:3001
LOGTO_ISSUER=http://127.0.0.1:3001/oidc
LOGTO_JWKS_URI=http://127.0.0.1:3001/oidc/jwks
LOGTO_API_RESOURCE=https://api.wisdom-tooth-ai.local
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://10.41.33.17:11434
OLLAMA_MODEL=qwen3.5:9b
OLLAMA_TIMEOUT_SECONDS=120
```

然后先执行数据库迁移，再进入后端目录启动服务：

```bash
.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head
```

再启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

建议你在 `backend` 目录下执行上面的 `uvicorn` 命令。

如果你启用了正式异步分析任务，还需要单独启动 Celery Worker：

```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

当前版本会优先调用本地 Ollama 多模态模型生成检测结果和中文报告；如果模型不可达或返回异常，会自动回退到内置 mock 分析结果。

### 3. 启动前端

在 `frontend` 目录执行：

```bash
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

并配置前端环境变量：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_LOGTO_ENDPOINT=http://127.0.0.1:3001
VITE_LOGTO_APP_ID=replace-with-your-logto-spa-app-id
VITE_LOGTO_API_RESOURCE=https://api.wisdom-tooth-ai.local
```

前端默认会通过 Vite 代理转发：

- `/api` -> `http://127.0.0.1:8000`
- `/ws` -> `ws://127.0.0.1:8000`

如果你想手动指定后端地址，可以在 `frontend/.env` 中添加：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 四、Docker 一键启动

如果你想直接把数据库、后端、前端全部启动起来，在仓库根目录执行：

```bash
docker-compose up --build
```

后台启动可使用：

```bash
docker-compose up -d --build
```

停止服务：

```bash
docker-compose down
```

如果你还想一起删除数据库卷：

```bash
docker-compose down -v
```

## 五、启动完成后的访问地址

启动成功后，可访问：

- 前端首页：`http://127.0.0.1:5173`
- 后端接口：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- PostgreSQL：`localhost:5432`

## 六、推荐启动顺序

推荐按下面顺序启动：

1. 启动 PostgreSQL
2. 启动后端 FastAPI
3. 启动前端 Vite
4. 打开前端页面进行上传、分析和审核测试

## 七、如何验证是否启动成功

### 1. 检查数据库容器

```bash
docker-compose ps
```

如果看到 `postgres` 为运行状态，说明数据库正常。

### 2. 检查后端健康接口

浏览器打开：

```text
http://127.0.0.1:8000/health
```

如果返回：

```json
{"status":"ok"}
```

说明后端正常。

### 3. 检查前端页面

浏览器打开：

```text
http://127.0.0.1:5173
```

如果能看到“智齿 AI 医生工作台”，说明前端正常。

### 4. 检查影像预览

上传一张图片后，在“AI 检测结果”区域应能看到影像预览。

如果浏览器无法直接预览该文件类型，界面会提示你通过文件接口下载查看。

### 4.1 调试上传接口

如果你想手动验证上传接口，不要手写 multipart body，直接使用 `curl -F`：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/images/upload" \
  -H "Authorization: Bearer <your-access-token>" \
  -F "file=@/path/to/head02.png" \
  -F "patient_id=P-0001" \
  -F "image_type=panoramic"
```

如果上传文件为空，后端会返回：`上传文件为空，请重新选择影像文件`。

### 5. 初始化 Logto 权限模型

打开 Logto 管理台：

```text
http://127.0.0.1:3002
```

按下面顺序配置：

- 创建 SPA 应用
- 回调地址：`http://127.0.0.1:5173/callback`
- 登出回跳地址：`http://127.0.0.1:5173/`
- 创建 API Resource：`https://api.wisdom-tooth-ai.local`
- 创建 scopes：
  - `read:images`
  - `upload:images`
  - `review:reports`
  - `finalize:reports`
- 创建 roles：
  - `radiologist`
  - `doctor`
  - `chief_doctor`
- 给角色授予对应 scope
- 给测试用户授予角色

当前系统内置的业务角色只有下面 3 个，并没有“病人”角色：

- `radiologist`
  - 中文含义：影像技师
  - 权限：`read:images`、`upload:images`
  - 用途：上传影像、查看分析记录和结果

- `doctor`
  - 中文含义：审核医生
  - 权限：`read:images`、`review:reports`
  - 用途：查看影像、提交医生审核意见

- `chief_doctor`
  - 中文含义：主任医生
  - 权限：`read:images`、`review:reports`、`finalize:reports`
  - 用途：查看影像、审核报告、正式确认报告

说明：

- 当前前端是“医生工作台”场景，不包含患者端功能。
- 如果用户没有被分配以上任一角色，前端会显示“暂无工作台访问权限”。
- 如果后续要支持患者端，需要单独设计新的角色、菜单和页面，不属于当前版本范围。

前端登录后，页面会展示当前 access token 中的 scope 列表。

同时系统会：

- 在页头展示当前角色
- 根据后端返回的菜单能力隐藏无权限模块
- 在无权访问某模块时显示专门的无权限提示页
- 在“权限说明”区域展示系统 RBAC 模型、角色与权限定义
- 优先使用 access token 中可识别的角色 claim，缺失时再按 scopes 推断角色
- 展示角色来源、角色 claim keys、claim 摘要和菜单映射，便于调试 Logto 配置

相关接口：

- `GET /api/v1/auth/me`
- `GET /api/v1/auth/rbac-model`

## 八、常见问题

### 1. 前端提示模块找不到

例如：

- `Cannot find module 'vue'`
- `Cannot find module 'axios'`
- `Cannot find module 'element-plus'`

处理方式：

```bash
npm install
```

### 2. 后端连不上数据库

请确认：

- PostgreSQL 容器已经启动
- `DATABASE_URL` 配置正确
- 端口 `5432` 没被其他数据库占用

可以先检查：

```bash
docker-compose ps
```

### 3. 5173 或 8000 端口被占用

请先关闭占用端口的进程，或者改启动端口。

### 4. Docker 启动失败

请确认：

- Docker Desktop 已启动
- `docker-compose` 可用
- 当前网络环境可以拉取镜像

### 5. 页面能打开，但接口报错

请优先检查：

- 后端是否已启动
- 浏览器里请求是否打到了 `/api`
- 后端控制台是否有报错日志

## 九、最常用的命令

### 本地开发

```bash
docker-compose up -d postgres
```

```bash
.venv\Scripts\python -m pip install -r backend\requirements.txt
```

```bash
npm install
```

### 一键启动

```bash
docker-compose up --build
```

## 十、补充说明

当前版本是 MVP：

- 已支持 PostgreSQL 持久化
- 已支持 Alembic 数据库迁移
- 已支持前后端联调
- 已支持 Docker 启动
- 已支持基础影像预览
- 已支持 MinIO 文件存储
- 已支持 Logto OSS 登录与 RBAC
- AI 检测结果仍为模拟数据

如果你愿意，下一步我也可以继续帮你补一份：

- `docs/deploy.md`：部署文档
- `docs/debug.md`：常见报错排查文档
- `docs/api.md`：接口使用文档
