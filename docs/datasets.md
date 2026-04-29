# 公开牙科影像数据集调研

本文档记录当前项目优先登记的数据集来源。系统只保存来源与元数据，不自动下载真实影像文件。

## 推荐优先级

| 优先级 | 数据集 | 适合任务 | 说明 |
| --- | --- | --- | --- |
| 高 | DENTEX 2023 Challenge | 牙位编号、龋齿、根尖病灶、智齿阻生 | 与当前系统检测类别最接近，优先用于论文说明和后续 baseline。 |
| 高 | OdontoAI O2PR | 牙齿实例分割、牙位编号 | 适合先做牙齿定位、编号和分割预训练。 |
| 中 | Tufts Dental Database | 异常检测、牙齿专家标注 | 数据量较清晰，但可能需要按平台要求申请。 |
| 中 | Mendeley Panoramic Dental Xray Dataset | 牙齿分割、编号 | 许可相对清晰，适合课程演示和 baseline。 |
| 中 | Pediatric Panoramic Caries Dataset | 儿童龋齿分割、疾病检测 | 可补充龋齿样本，但儿童场景需单独评估。 |
| 低 | Panoramic Mandible Segmentation | 下颌骨分割 | 对智齿主线帮助较间接，可作为解剖结构分割扩展。 |

## 来源清单

- DENTEX 2023：Grand Challenge `https://dentex.grand-challenge.org/data/`，Zenodo `https://zenodo.org/records/7812323`，Kaggle 镜像 `https://www.kaggle.com/datasets/truthisneverlinear/dentex-challenge-2023`。
- OdontoAI O2PR：GitHub `https://github.com/IvisionLab/OdontoAI-Open-Panoramic-Radiographs`，MEDIA-datasets `https://github.com/IvisionLab/MEDIA-datasets`。
- Tufts Dental Database：OJP `https://www.ojp.gov/library/publications/tufts-dental-database-multimodal-panoramic-x-ray-dataset-benchmarking`，NIDCR Data Hub `https://www.ddshub.nih.gov/data-sources/head-neck-imaging-data`。
- Mendeley Panoramic Dental Xray Dataset：`https://data.mendeley.com/datasets/73n3kz2k4k`。
- Panoramic Mandible Segmentation：`https://data.mendeley.com/datasets/hxt48yk462/2`。
- Pediatric Panoramic Caries Dataset：Mendeley 索引 `https://www.mendeley.com/catalogue/4b6db210-87eb-3ceb-8363-b10509556d42/`。

## 使用建议

- 第一阶段只做登记与引用，记录许可、访问状态、任务类型、病种标签和样本规模。
- 第二阶段支持本地目录登记、手动统计录入和小型 zip 样本包上传；真实大型公开数据不要提交到仓库。
- zip 上传第一版只做 MinIO 存储和文件名索引，不做完整 COCO/VOC/DICOM 解析。
- 训练集划分第一版只写数据库中的 `train/val/test` 标记，不移动真实文件。
- 训练前需要单独确认各数据集许可，尤其是非商业许可、注册访问和需申请的数据源。
- DENTEX 优先映射到当前系统类别：`caries`、`deep caries`、`periapical lesions`、`impacted teeth`。
