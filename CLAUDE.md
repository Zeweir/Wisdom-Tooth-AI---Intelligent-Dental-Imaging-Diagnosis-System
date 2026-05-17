# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Docker (full stack)

```bash
docker compose up -d --build          # 启动全部 7 个服务
docker compose -f docker-compose.prod.yml up -d  # 生产模式（使用预构建镜像）
```

### 后端 (FastAPI)

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head                  # 数据库迁移
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
celery -A app.celery_app.celery_app worker --loglevel=info  # Celery worker
```

### 前端

```bash
cd frontend
npm install
npm run dev                           # 开发服务器
npm run type-check                    # vue-tsc 类型检查
npm run build                         # 类型检查 + 构建
```

`VITE_API_BASE_URL` 环境变量控制后端地址，默认为空（同源直连）。本地开发时在 `frontend/.env.local` 配置 `VITE_API_BASE_URL=http://127.0.0.1:8000`。

### CI

PR 提交自动触发 `ci.yml`：前端 `vue-tsc --noEmit` + `vite build`，后端 `compileall` + JWT 鉴权单元测试。Push 到 main 自动触发 `release.yml` 构建 Docker 镜像并推送到 `ghcr.io`。

## 架构总览

### 后端分析管道

```
上传影像 → Celery 任务 (run_image_analysis)
  → YOLOv8 牙片检测 (可选，失败回退)
  → Ollama 多模态报告生成 (可选，失败回退)
  → mock 兜底生成假检测结果
  → ReportLab 生成 PDF 报告
```

分析结果写入 `image_records.detections` (JSON) 和 `report_records.structured_content` (JSON)，PDF 输出到 MinIO 或本地存储。

- [backend/app/services.py](backend/app/services.py) — 分析编排核心 (`generate_analysis_result` → `finalize_image_record`)
- [backend/app/clinical_reports.py](backend/app/clinical_reports.py) — 牙科领域知识库：FDI 牙位推断、病灶释义匹配、结构化报告构建
- [backend/app/tasks.py](backend/app/tasks.py) — Celery 异步任务定义
- [backend/app/yolo.py](backend/app/yolo.py) — YOLO 模型封装
- [backend/app/ollama.py](backend/app/ollama.py) — Ollama 多模态调用封装
- [backend/app/pdf_reports.py](backend/app/pdf_reports.py) — ReportLab PDF 生成

### 数据模型关系

`ImageRecord` 1:1 → `ReportRecord`，`ReportRecord` 1:N → `ReportRevisionRecord`（每次审核/确认创建快照）。`ImageRecord` N:1 → `PatientRecord`。`DatasetCatalogRecord` 1:N → `DatasetImportRecord` 1:N → `DatasetSampleRecord`。`ModelEvaluationRecord` 关联数据集和导入批次。

### 鉴权体系

JWT (HS256) + bcrypt 密码哈希，自建用户表 `users`。三个角色定义在 [backend/app/auth.py](backend/app/auth.py#L38-L57)：

- `radiologist` (影像技师): `read:images`, `upload:images`
- `doctor` (审核医生): `read:images`, `review:reports`
- `chief_doctor` (主任医生): 全部 4 个 scope，含 `finalize:reports`

前端全局状态通过 [frontend/src/composables/useAuth.ts](frontend/src/composables/useAuth.ts) 管理，Token 存储在 `localStorage`。路由守卫检查 token 存在即放行——特定页面的权限控制由页面内部根据 `authProfile.menus[].visible` 判断。

### 前端路由与菜单

路由表在 [frontend/src/router/index.ts](frontend/src/router/index.ts)。`/upload`、`/diagnosis`、`/reports` 三个路径重定向到 `/workspace`（影像工作站是合并页面）。侧边栏菜单项和可见性由后端 `/api/v1/auth/me` 返回的 `menus` 数组控制，不在前端硬编码。

### 存储抽象

[backend/app/storage.py](backend/app/storage.py) 的 `StorageService` 根据 `STORAGE_PROVIDER` 环境变量决定使用 MinIO 或本地文件系统。所有影像上传、数据集导入、PDF 报告均通过该服务写入。

### 报告审核与版本管理

审核流程：AI 生成草稿 (`ai_generated`) → 医生审核 (`doctor_reviewed`) → 主任正式确认 (`finalized`)。每次审核/确认操作创建一条 `ReportRevisionRecord` 快照，同时重新生成 PDF。审核时可修改检测结果 (`modified_findings`)。

### miniapp 目录

`miniapp/` 是独立的微信小程序项目（Taro 框架），与主项目后端使用同一套 API。有独立的 `package.json`、构建配置和 `dist/` 输出目录。`miniapp/` 已加入 `.gitignore` 例外，暂未提交到仓库。

### 服务拓扑 (Docker Compose)

```
gateway (Nginx :80/:443)
  ├── frontend (Vue SPA :80)
  ├── /api/* → backend (FastAPI :8000)
  └── /ws/* → backend (WebSocket)
backend
  ├── postgres:5432
  ├── minio:9000
  └── redis:6379
celery-worker
  └── redis:6379 (broker)
```
