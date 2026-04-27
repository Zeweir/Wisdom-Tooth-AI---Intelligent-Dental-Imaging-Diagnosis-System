🦷 智齿 AI — 牙齿影像智能诊断系统

开发文档 V2.0

## 一、项目定位

### 1.1 项目背景

口腔影像诊断对医生经验依赖较强，而基层口腔机构往往缺少稳定的影像判读能力。本项目目标是构建一套面向牙科影像场景的智能辅助诊断系统，对全景片、根尖片等影像进行自动分析，并生成可供医生审核的中文诊断报告。

本系统定位为 **辅助诊断平台**，不直接替代医生诊断。AI 输出结果必须经过医生确认后方可作为正式报告内容。

### 1.2 项目目标

- 支持牙齿影像上传、存储、分析与结果回查
- 支持常见口腔病变的检测、分类与可视化展示
- 基于结构化 AI 结果生成中文诊断报告
- 支持医生审核、修订和最终确认
- 提供可持续扩展的全栈架构，便于后续增加小程序、HIS 对接和 CBCT 模块

### 1.3 第一阶段建设原则

- 单仓多模块，降低初期协作与联调成本
- 先做 Web 医生工作台，不优先做小程序
- 先打通主链路，再逐步增强模型能力
- 大模型优先本地部署，避免依赖外部 API
- 以 MVP 为目标，避免过度设计

---
## 二、推荐技术路线

### 2.1 技术栈总览

| 层级 | 推荐技术 | 说明 |
|------|----------|------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus | 适合后台管理、医生审核台、报告管理 |
| 前端状态 | Pinia + Vue Router + Axios | 状态管理、路由、接口请求 |
| 后端 API | FastAPI + SQLAlchemy + Alembic | 开发效率高，适合 AI 场景与接口联调 |
| AI 推理 | Python + PyTorch + ONNX Runtime | 模型训练与推理统一 Python 生态 |
| 大模型 | Ollama 本地部署 | 使用本地模型生成中文诊断报告，不依赖第三方 API |
| 任务队列 | Celery + RabbitMQ | 异步分析、任务状态流转、失败重试 |
| 数据库 | PostgreSQL | 核心业务数据、结构化结果、JSONB |
| 对象存储 | MinIO | 原始影像、缩略图、分割图、导出 PDF |
| 缓存 | Redis | 会话、热点数据、任务状态缓存 |
| 网关 | Nginx | 反向代理、静态资源分发、上传转发 |
| 容器化 | Docker Compose | 适合本地开发与第一阶段部署 |
| 监控 | Prometheus + Grafana | 第二阶段引入 |

### 2.2 为什么优先选择这套方案

#### 后端优先用 FastAPI

- AI 处理、DICOM 解析、图像预处理本身就在 Python 生态中
- 与 PyTorch、ONNX Runtime、Ollama 集成更自然
- 支持文件上传、异步接口、WebSocket、自动接口文档
- 比 Go 更适合本项目第一阶段的快速落地

#### 前端优先用 Vue 3 + Element Plus

- 医生工作台和管理后台场景更适合中后台组件库
- 表格、表单、上传、对话框等组件成熟
- 能快速搭建审核页面、影像列表、报告详情页

#### 大模型优先本地走 Ollama

- 不依赖外部 API Key
- 便于本地开发与离线环境测试
- 更适合医疗数据场景下的隐私要求
- 建议先采用“结构化结果 + 文本生成”的模式，而不是一开始直接做端到端视觉大模型看片

---
三、数据层设计

3.1 数据库设计（核心表）

UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID REFERENCES dental_images(id),
    ai_analysis_id UUID REFERENCES ai_analysis(id),
    doctor_id UUID REFERENCES users(id),
    report_content TEXT,  -- 大模型生成的报告
    doctor_review TEXT,  -- 医生审核意见
    status VARCHAR(20) DEFAULT 'ai_generated' CHECK (status IN ('ai_generated', 'doctor_reviewed', 'finalized')),
    created_at TIMESTAMP DEFAULT NOW()
);
```

3.2 影像存储规范

- 原始影像：MinIO对象存储，按 `/{hospital_id}/{patient_id}/{date}/{image_id}.dcm` 组织
- 预处理影像：缩略图、标准化后的图像
- AI标注结果：JSON格式，包含bbox坐标、mask、类别标签
- 报告PDF：生成后存储，支持下载

---

四、AI模型层设计

4.1 影像预处理流水线

```
原始影像 → 格式转换(DICOM→PNG) → 去噪/增强 → 尺寸标准化 
    → 对比度增强(CLAHE) → 归一化 → 输入模型
```

4.2 视觉模型架构

采用两阶段检测+分割方案：

| 任务 | 模型 | 输入 | 输出 |
|------|------|------|------|
| 牙齿检测 | YOLOv8 / RT-DETR | 全景片/根尖片 | 牙齿边界框 + 类别（切牙、磨牙等） |
| 病变检测 | YOLOv8-seg / MMDetection | 单颗牙齿ROI | 龋齿、根尖阴影、牙周膜增宽等 |
| 牙齿分割 | SAM / U-Net | 全口影像 | 每颗牙齿的精确mask |
| 牙槽骨分割 | U-Net++ / nnU-Net | CBCT切片 | 牙槽骨高度、密度分析 |

4.3 疾病识别类别

```yaml
disease_classes:
  - id: 1
    name: "龋齿"
    severity: ["浅龋", "中龋", "深龋"]
    locations: ["牙冠", "牙颈部", "邻面"]
  
  - id: 2
    name: "牙周炎"
    severity: ["轻度", "中度", "重度"]
    indicators: ["牙槽骨吸收", "牙周膜增宽"]
  
  - id: 3
    name: "根尖周炎"
    severity: ["急性", "慢性"]
    indicators: ["根尖阴影", "根尖周骨质破坏"]
  
  - id: 4
    name: "智齿阻生"
    severity: ["垂直阻生", "水平阻生", "近中阻生", "远中阻生"]
    indicators: ["邻牙压迫", "囊肿风险"]
  
  - id: 5
    name: "牙体缺损"
    severity: ["釉质缺损", "牙本质缺损", "牙髓暴露"]
  
  - id: 6
    name: "牙结石"
    severity: ["Ⅰ度", "Ⅱ度", "Ⅲ度"]
  
  - id: 7
    name: "牙根吸收"
    severity: ["外吸收", "内吸收"]
```

4.4 大模型诊断模块

方案A：多模态大模型（推荐）

- 使用支持视觉输入的大模型（如 Qwen2.5-VL、DeepSeek-VL）
- 输入：牙齿影像 + 结构化检测结果（JSON）
- 输出：中文诊断报告

方案B：视觉模型 + LLM 分离

- 视觉模型提取特征 → 结构化结果
- LLM（如 DeepSeek、ChatGLM）基于结构化结果生成报告

Prompt模板示例：

```python
DIAGNOSIS_PROMPT = """
你是一位资深口腔科专家。请根据以下牙齿影像的AI分析结果，撰写一份专业的中文诊断报告。

【患者信息】
性别：{gender}，年龄：{age}岁

【影像类型】{image_type}

【AI检测结果】
{detections_json}

【要求】
1. 报告结构包含：影像描述、诊断意见、严重程度评估、治疗建议、注意事项
2. 使用专业但通俗的语言，患者也能理解
3. 对不确定的发现标注"建议进一步检查"
4. 报告字数控制在300-500字
5. 如果有多种病变，按严重程度排序

请直接输出报告内容：
"""
```

---

五、API接口设计

5.1 核心接口

1. 影像上传

```http
POST /api/v1/images/upload
Content-Type: multipart/form-data

Request:
  - file: 影像文件
  - patient_id: 患者ID
  - image_type: panoramic | periapical | cbct

Response:
{
  "code": 200,
  "data": {
    "image_id": "uuid",
    "status": "processing",
    "message": "影像已接收，正在分析"
  }
}
```

1. 查询分析结果

```http
GET /api/v1/analysis/{image_id}

Response:
{
  "code": 200,
  "data": {
    "image_id": "uuid",
    "status": "completed",
    "detections": [
      {
        "bbox": [x1, y1, x2, y2],
        "class": "龋齿",
        "confidence": 0.94,
        "severity": "中龋",
        "tooth_id": "36"
      }
    ],
    "segmentation_url": "https://minio/.../mask.png",
    "report": {
      "content": "影像显示：左下第一磨牙（36）可见中龋...",
      "doctor_review": null,
      "status": "ai_generated"
    }
  }
}
```

1. 医生审核报告

```http
PUT /api/v1/reports/{report_id}/review

Request:
{
  "doctor_review": "AI诊断基本准确，建议补充根尖片确认根尖状态",
  "modified_findings": [...],
  "status": "doctor_reviewed"
}
```

1. 实时分析（WebSocket）

```http
WS /ws/analysis/{image_id}

推送事件：
- image.received  影像已接收
- ai.detecting    AI检测中
- ai.completed    AI分析完成
- report.generated 报告已生成
```

---

六、开发计划

6.1 里程碑规划

| 阶段 | 周期 | 交付物 |
|------|------|--------|
| Phase 1: 基础架构 | 2周 | 项目脚手架、数据库、MinIO、基础API |
| Phase 2: 数据准备 | 3周 | 数据采集（公开数据集+合作医院）、标注、数据增强 |
| Phase 3: 视觉模型 | 4周 | 牙齿检测、病变检测、分割模型训练与优化 |
| Phase 4: 大模型集成 | 2周 | Prompt工程、RAG知识库、报告生成 |
| Phase 5: 前端开发 | 3周 | Web管理端、医生审核界面、报告展示 |
| Phase 6: 集成测试 | 2周 | 端到端测试、性能优化、安全审计 |
| Phase 7: 部署上线 | 1周 | K8s部署、监控配置、灰度发布 |

6.2 推荐数据集

| 数据集 | 内容 | 用途 |
|--------|------|------|
| DENTEX | 全景片牙齿检测与分割 | 牙齿定位、编号 |
| TUFTS Dental | 多种口腔疾病标注 | 龋齿、牙周病检测 |
| Panoramic Radiographs | 全景片公开数据集 | 预训练 |
| 私有医院数据 | 真实临床影像（需脱敏） | 微调、提升准确率 |

---

七、关键技术难点与解决方案

7.1 医学影像特殊性

- 问题：DICOM格式多样、分辨率差异大、金属伪影干扰
- 解决：统一预处理pipeline，金属伪影抑制算法，多尺度训练

7.2 小样本学习

- 问题：某些罕见病变样本极少
- 解决：数据增强（MixUp、CutMix）、迁移学习、半监督学习

7.3 大模型幻觉

- 问题：LLM可能生成不存在的诊断
- 解决：RAG检索增强（接入口腔医学知识库）、结构化输出约束、医生审核机制

7.4 实时性要求

- 问题：影像分析需快速响应
- 解决：模型量化(INT8)、TensorRT加速、异步队列处理、GPU集群

---

八、合规与安全

8.1 医疗合规

- 系统定位为辅助诊断工具，报告需医生签字确认，不可直接作为诊断依据
- 符合《医疗器械监督管理条例》，如需上市需申请二类医疗器械注册证
- 患者数据脱敏处理，符合《个人信息保护法》《数据安全法》

8.2 系统安全

- 影像传输使用TLS加密
- API接口JWT认证 + RBAC权限控制
- 操作日志全量审计
- 模型推理结果可解释性（热力图、注意力可视化）

---

九、部署架构

9.1 生产环境配置

```yaml
docker-compose.yml 示例
services:
  api:
    image: dental-ai-api:latest
    replicas: 3
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
  
  ai-inference:
    image: dental-ai-model:latest
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=0,1
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]
  
  llm-service:
    image: qwen2.5-vl:latest
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=2,3
  
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
  
  postgres:
    image: postgres:15
    volumes:
      - pg_data:/var/lib/postgresql/data
```

---

十、后续迭代方向

1. 三维CBCT分析：从2D全景片扩展到3D CBCT全口重建
2. 治疗路径推荐：结合患者历史数据推荐个性化治疗方案
3. 预后评估：基于影像变化预测疾病发展趋势
4. 多模态融合：结合口内照、病史文本综合诊断
5. 边缘计算：部署轻量化模型到口腔CBCT设备端，实现本地实时分析

---

如需进一步细化某个模块（如具体模型训练代码、前端原型、数据库ER图、API详细文档），可以告诉我，我可以继续深入展开！
