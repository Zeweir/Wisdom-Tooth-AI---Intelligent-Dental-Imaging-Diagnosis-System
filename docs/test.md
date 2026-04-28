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

- `/` 首页摘要、影像类型分布、临床流程卡片正常展示。
- `/workspace` 上传区、分页病例列表、影像预览、检测框、报告审核、报告打印和 HTML 导出正常。
- `/access` 权限中心在有权限和无权限状态下都不破版。
- `/audit` 审计日志分页、高级筛选、刷新按钮正常。

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
- `/api/v1/images`
- `/api/v1/audit-logs`
- `/api/v1/reports/{report_id}/review`

## 联调验证

按下面顺序验证主链路：

1. 启动 PostgreSQL、Redis、MinIO、后端、Celery Worker 和前端。
2. 使用 Logto 登录具备 `read:images`、`upload:images`、`review:reports` 的账号。
3. 上传影像，确认 WebSocket 事件和列表分页刷新。
4. 选择病例，确认影像预览、检测框和置信度展示。
5. 提交医生审核意见，确认报告状态变为医生已审核。
6. 使用具备 `finalize:reports` 的账号正式确认报告。
7. 进入审计中心，按动作、资源类型、资源 ID 或操作者筛选日志。

## 回归场景

- 未登录时只能看到登录提示。
- 仅 `upload:images` 权限不可查看记录详情。
- 仅 `read:images` 权限可查看影像但不可审核。
- `doctor` 可审核但不可正式确认。
- `chief_doctor` 可审核并正式确认。
