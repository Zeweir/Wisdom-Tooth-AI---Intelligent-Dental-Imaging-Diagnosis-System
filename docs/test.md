# 测试与验证文档

本文档记录当前 MVP 的最小验证流程。

## 前端验证

在 `frontend` 目录执行：

```bash
npm.cmd run type-check
```

```bash
npm.cmd run build
```

需要手动检查：

- `/` 首页摘要、患者指标、当前病例入口正常展示。
- `/workspace` 三步流程清晰展示，上传区、病例列表、影像预览、检测框、报告审核、报告打印和 HTML 导出正常。
- `/workspace?image_id=<id>` 能直接打开指定病例；从首页最近病例和患者历史病例进入时应选中同一病例。
- `/patients` 患者列表、搜索、新建/编辑、患者病例时间线、报告预览抽屉和工作站深链接正常。
- `/datasets` 数据集初始化入口可见；无 `upload:images` 时显示禁用说明，有权限时可初始化、搜索、筛选、新建/编辑、创建导入批次、浏览样本、训练集划分和登记模型评估。
- `/access` 权限中心在有权限和无权限状态下都不破版。
- `/audit` 审计日志分页、高级筛选、快捷筛选和刷新按钮正常。

Docker 场景下应通过 `http://127.0.0.1:5173/api/v1/auth/me` 访问后端代理；未登录时应返回 `401 Authorization header is missing`，不应返回 `404 Not Found`。

## 后端验证

在 `backend` 目录执行：

```bash
..\.venv\Scripts\python.exe -m compileall app
```

检查 OpenAPI 是否能生成：

```bash
..\.venv\Scripts\python.exe -c "from app.main import app; print('\n'.join(sorted(app.openapi()['paths'].keys())))"
```

需要确认输出包含：

- `/api/v1/dashboard/summary`
- `/api/v1/patients`
- `/api/v1/patients/{patient_id}`
- `/api/v1/patients/{patient_id}/images`
- `/api/v1/datasets`
- `/api/v1/datasets/seed-public`
- `/api/v1/datasets/{dataset_id}`
- `/api/v1/datasets/{dataset_id}/imports`
- `/api/v1/dataset-imports/{import_id}/samples`
- `/api/v1/dataset-imports/{import_id}/split`
- `/api/v1/model-evaluations`
- `/api/v1/images`
- `/api/v1/audit-logs`
- `/api/v1/reports/{report_id}/review`

## 联调验证

按下面顺序验证主链路：

1. 启动 PostgreSQL、Redis、MinIO、后端、Celery Worker 和前端。
2. 使用 Logto 登录具备 `read:images`、`upload:images`、`review:reports` 的账号。
3. 上传影像，确认 WebSocket 事件和列表分页刷新。
4. 进入患者档案，新建患者并验证搜索、编辑和病例时间线。
5. 进入数据集中心，执行公开清单初始化，验证 DENTEX、OdontoAI、Tufts 等登记可搜索和查看详情。
6. 为 DENTEX 创建本地目录导入、手动统计导入和小型 zip 上传导入。
7. 查看样本索引，执行 `70/15/15` 训练集划分，新增模型评估记录。
8. 在工作站上传影像时选择已有患者或输入新患者编号，确认患者档案自动绑定。
9. 选择病例，确认影像预览、检测框和置信度展示。
10. 提交医生审核意见，确认报告状态变为医生已审核。
11. 使用具备 `finalize:reports` 的账号正式确认报告。
12. 返回患者档案，打开该病例的报告预览，确认报告状态、AI 草稿、医生意见和更新时间展示正确。
13. 通过患者历史病例的“打开病例”进入 `/workspace?image_id=<id>`，确认工作站选中同一病例。
14. 进入审计中心，使用“报告审核”“正式确认”“数据集导入”“患者更新”等快捷筛选验证日志刷新。

## 回归场景

- 未登录时只能看到登录提示。
- 仅 `upload:images` 权限不可查看记录详情。
- 仅 `read:images` 权限可查看影像、患者档案和数据集中心但不可编辑。
- `doctor` 可审核但不可正式确认。
- `chief_doctor` 可审核并正式确认。
- 只读医生可以查看患者历史报告预览，但不能保存审核意见或正式确认。
