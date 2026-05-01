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
- 返回影像总数、患者总数、近 7 天新增患者、待审核病例、处理中数量、已完成数量、病灶数量、平均置信度、报告状态分布、影像类型分布、审计事件数和最新病例。

## 患者档案

- `GET /api/v1/patients`
- 需要 `read:images`。
- Query：`keyword`、`limit`、`offset`。
- 返回分页后的患者档案，包含影像数量和最近影像时间。

- `POST /api/v1/patients`
- 需要 `upload:images`。
- Body：`patient_id`、`name`、`gender`、`age`、`phone`、`notes`。
- 创建患者基础档案。

- `GET /api/v1/patients/{patient_id}`
- 需要 `read:images`。
- 返回患者详情和病例统计。

- `PUT /api/v1/patients/{patient_id}`
- 需要 `upload:images`。
- Body：`name`、`gender`、`age`、`phone`、`notes`。
- 更新患者基础档案。

- `GET /api/v1/patients/{patient_id}/images`
- 需要 `read:images`。
- Query：`limit`、`offset`。
- 返回该患者的分页影像记录。

## 数据集中心

- `GET /api/v1/datasets`
- 需要 `read:images`。
- Query：`keyword`、`task_type`、`disease`、`limit`、`offset`。
- 返回分页后的公开数据集登记，包含来源、许可、任务类型、病种标签和访问状态。

- `POST /api/v1/datasets`
- 需要 `upload:images`。
- Body：`name`、`source_name`、`homepage_url`、`paper_url`、`license`、`image_type`、`task_types`、`disease_tags`、`sample_size`、`annotation_format`、`access_status`、`priority`、`notes`。
- 新增一个数据集来源登记，不上传真实影像文件。

- `POST /api/v1/datasets/seed-public`
- 需要 `upload:images`。
- 写入内置公开数据集清单；重复执行会跳过已存在的数据集。

- `GET /api/v1/datasets/{dataset_id}`
- 需要 `read:images`。
- 返回单个数据集登记详情。

- `PUT /api/v1/datasets/{dataset_id}`
- 需要 `upload:images`。
- 更新数据集登记字段。

- `GET /api/v1/datasets/{dataset_id}/imports`
- 需要 `read:images`。
- 返回该数据集的导入批次。

- `POST /api/v1/datasets/{dataset_id}/imports`
- 需要 `upload:images`。
- Body：`import_method`、`source_path`、`sample_count`、`annotation_format`、`image_type`、`notes`。
- 支持 `local_directory`、`zip_upload`、`manual_summary`、`url_download`。

- `POST /api/v1/datasets/{dataset_id}/imports/download-url`
- 需要 `upload:images`。
- Body：`source_url`、`sample_count`、`annotation_format`、`image_type`、`notes`。
- 下载可匿名访问的公开 zip 直链，保存到对象存储/本地存储，并复用 zip 索引逻辑生成样本索引。Kaggle 页面地址通常不是 zip 直链。

- `POST /api/v1/dataset-imports/{import_id}/upload-zip`
- 需要 `upload:images`。
- FormData：`file`，仅支持 zip 样本包；第一版只做存储和文件名索引。

- `GET /api/v1/dataset-imports/{import_id}/samples`
- 需要 `read:images`。
- Query：`limit`、`offset`。
- 返回样本索引列表。

- `POST /api/v1/dataset-imports/{import_id}/split`
- 需要 `upload:images`。
- Body：`train_ratio`、`val_ratio`、`test_ratio`。
- 默认按 `70/15/15` 写入样本划分标记。

## 模型评估

- `GET /api/v1/model-evaluations`
- 需要 `read:images`。
- Query：`dataset_id`、`import_id`、`limit`、`offset`。
- 返回模型评估记录。

- `POST /api/v1/model-evaluations`
- 需要 `upload:images`。
- Body：`model_name`、`model_version`、`dataset_id`、`import_id`、`precision`、`recall`、`map_score`、`f1_score`、`sample_count`、`notes`。

## 影像与分析

- `GET /api/v1/images`
- 需要 `read:images`。
- Query：`patient_id`、`image_type`、`report_status`、`limit`、`offset`。
- 返回分页后的影像分析记录。

- `POST /api/v1/images/upload`
- 需要 `upload:images`。
- FormData：`file`、`patient_id`、`image_type`、可选 `patient_name`。
- 上传时如果患者档案不存在，会自动创建最小患者档案。
- 返回新影像 `image_id` 和处理状态。后台分析优先使用配置的 YOLO 权重；未配置或推理失败时回退到 Ollama / mock。

- `GET /api/v1/analysis/{image_id}`
- 需要 `read:images`。
- 返回单个影像分析详情。
- 前端工作站支持通过 `/workspace?image_id=<image_id>` 直接打开该影像分析详情，该能力复用本接口，不新增后端路由。

- `GET /api/v1/images/{image_id}/file`
- 需要 `read:images`。
- 返回原始影像文件内容。

## 报告审核

- `PUT /api/v1/reports/{report_id}/review`
- 需要 `review:reports`；正式确认还需要 `finalize:reports`。
- Body：`doctor_review`、`modified_findings`、`status`。
- `status` 可为 `doctor_reviewed` 或 `finalized`。
- 患者档案中的报告预览复用影像详情中的 `report.content`、`report.doctor_review`、`report.status` 和检测结果，不新增报告预览接口。
- 成功保存审核意见或正式确认后，后端会自动写入一条报告版本快照，并记录 `report.revision_created` 审计事件。

- `GET /api/v1/reports/{report_id}/revisions`
- 需要 `read:images`。
- Query：`limit`、`offset`。
- 返回分页报告版本历史，字段包括 `revision_id`、`report_id`、`image_id`、`version_no`、`status`、`content`、`doctor_review`、`detections`、`actor_sub`、`actor_roles`、`created_at`。
- 版本历史用于工作站和患者档案复核报告从 AI 草稿、医生审核到正式确认的流转过程。

## 审计日志

- `GET /api/v1/audit-logs`
- 需要 `review:reports`。
- Query：`limit`、`offset`、`action`、`resource_type`、`resource_id`、`actor_sub`。
- 返回分页后的审计日志。
- 前端审计中心提供报告审核、正式确认、报告版本记录、数据集导入、样本包上传、训练集划分、模型评估、患者更新、影像上传等快捷筛选，本质仍是填充上述 Query 参数。

## WebSocket

- `WS /ws/analysis/{image_id}`
- Query：`access_token`。
- 推送 `image.received`、`ai.detecting`、`ai.completed`、`report.generated` 等事件。
