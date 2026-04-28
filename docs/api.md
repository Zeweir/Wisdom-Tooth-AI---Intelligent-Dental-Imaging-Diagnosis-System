# API 使用文档

本文档记录当前 MVP 的主要接口。所有业务接口默认返回：

```json
{
  "code": 200,
  "data": {}
}
```

列表接口会额外返回分页信息：

```json
{
  "code": 200,
  "data": [],
  "meta": {
    "limit": 10,
    "offset": 0,
    "total": 42
  }
}
```

## 认证与权限

- `GET /api/v1/auth/me`：当前访问画像、权限、角色和菜单可见性。
- `GET /api/v1/auth/rbac-model`：系统 RBAC 权限模型说明。

## 工作台摘要

- `GET /api/v1/dashboard/summary`
- 需要 `read:images`。
- 返回影像总数、处理中数量、已完成数量、病灶数量、平均置信度、报告状态分布、影像类型分布、审计事件数和最新病例。

## 影像与分析

- `GET /api/v1/images`
- 需要 `read:images`。
- Query：`patient_id`、`image_type`、`report_status`、`limit`、`offset`。
- 返回分页后的影像分析记录。

- `POST /api/v1/images/upload`
- 需要 `upload:images`。
- FormData：`file`、`patient_id`、`image_type`。
- 返回新影像 `image_id` 和处理状态。

- `GET /api/v1/analysis/{image_id}`
- 需要 `read:images`。
- 返回单个影像分析详情。

- `GET /api/v1/images/{image_id}/file`
- 需要 `read:images`。
- 返回原始影像文件内容。

## 报告审核

- `PUT /api/v1/reports/{report_id}/review`
- 需要 `review:reports`；正式确认还需要 `finalize:reports`。
- Body：`doctor_review`、`modified_findings`、`status`。
- `status` 可为 `doctor_reviewed` 或 `finalized`。

## 审计日志

- `GET /api/v1/audit-logs`
- 需要 `review:reports`。
- Query：`limit`、`offset`、`action`、`resource_type`、`resource_id`、`actor_sub`。
- 返回分页后的审计日志。

## WebSocket

- `WS /ws/analysis/{image_id}`
- Query：`access_token`。
- 推送 `image.received`、`ai.detecting`、`ai.completed`、`report.generated` 等事件。
