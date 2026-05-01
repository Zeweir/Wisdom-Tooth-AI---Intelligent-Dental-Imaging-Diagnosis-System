<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import {
  createDataset,
  createDatasetImport,
  createModelEvaluation,
  downloadDatasetZip,
  listDatasetImports,
  listDatasetSamples,
  listDatasets,
  listModelEvaluations,
  seedPublicDatasets,
  splitDatasetImport,
  updateDataset,
  uploadDatasetZip,
} from '../api/datasets'
import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import type { PaginationMeta } from '../types/analysis'
import type {
  DatasetCatalog,
  DatasetCatalogPayload,
  DatasetImportPayload,
  DatasetImportRecord,
  DatasetSampleRecord,
  ModelEvaluationPayload,
  ModelEvaluationRecord,
} from '../types/dataset'
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()
const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const canReadImages = workbench.canReadImages
const canUpload = workbench.canUpload
const beginSignOut = workbench.beginSignOut
const refreshDashboardSummary = workbench.refreshDashboardSummary

const datasets = ref<DatasetCatalog[]>([])
const selectedDataset = ref<DatasetCatalog | null>(null)
const selectedImport = ref<DatasetImportRecord | null>(null)
const imports = ref<DatasetImportRecord[]>([])
const samples = ref<DatasetSampleRecord[]>([])
const evaluations = ref<ModelEvaluationRecord[]>([])
const loading = ref(false)
const importsLoading = ref(false)
const samplesLoading = ref(false)
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const evaluationDialogVisible = ref(false)
const detailVisible = ref(false)
const samplesDrawerVisible = ref(false)
const activeDatasetTab = ref('imports')
const editingDataset = ref<DatasetCatalog | null>(null)
const filters = reactive({
  keyword: '',
  task_type: '',
  disease: '',
})
const pagination = ref<PaginationMeta>({ limit: 9, offset: 0, total: 0 })
const importsPagination = ref<PaginationMeta>({ limit: 8, offset: 0, total: 0 })
const samplesPagination = ref<PaginationMeta>({ limit: 10, offset: 0, total: 0 })
const evaluationsPagination = ref<PaginationMeta>({ limit: 8, offset: 0, total: 0 })
const form = reactive<DatasetCatalogPayload>({
  name: '',
  source_name: '',
  homepage_url: '',
  paper_url: '',
  license: '',
  image_type: 'panoramic',
  task_types: [],
  disease_tags: [],
  sample_size: '',
  annotation_format: '',
  access_status: 'open',
  priority: 'medium',
  notes: '',
})
const importForm = reactive<DatasetImportPayload>({
  import_method: 'local_directory',
  source_path: '',
  sample_count: 0,
  annotation_format: '',
  image_type: 'panoramic',
  notes: '',
})
const evaluationForm = reactive<ModelEvaluationPayload>({
  model_name: '',
  model_version: '',
  dataset_id: null,
  import_id: null,
  precision: null,
  recall: null,
  map_score: null,
  f1_score: null,
  sample_count: null,
  notes: '',
})
const zipFile = ref<File | null>(null)

const totalDiseaseTags = computed(() => new Set(datasets.value.flatMap((item) => item.disease_tags)).size)
const openDatasetCount = computed(() => datasets.value.filter((item) => ['open', 'open_reference', 'open_registration'].includes(item.access_status)).length)
const highPriorityDatasetCount = computed(() => datasets.value.filter((item) => item.priority === 'high').length)
const featuredDataset = computed(() => {
  return datasets.value.find((item) => /child|pediatric|yolo|儿童|caries/i.test(`${item.name} ${item.notes ?? ''}`))
    ?? selectedDataset.value
    ?? datasets.value[0]
    ?? null
})
const selectedDatasetMetrics = computed(() => [
  {
    label: '导入批次',
    value: imports.value.length,
  },
  {
    label: '当前样本',
    value: imports.value.reduce((sum, item) => sum + item.sample_count, 0),
  },
  {
    label: '评估记录',
    value: evaluations.value.length,
  },
])
const datasetPipelineSteps = [
  {
    title: '登记公开来源',
    description: '记录 Kaggle、GitHub、论文或医疗影像设备来源，明确许可与任务适配范围。',
  },
  {
    title: '导入样本索引',
    description: '登记本地目录、上传 zip、公开直链下载或录入手动统计，系统索引影像与 YOLO/COCO 等标注文件。',
  },
  {
    title: '划分训练集合',
    description: '按 70/15/15 生成 train、val、test 标记，为 YOLOv8-C2f-CBAM 等模型实验准备数据。',
  },
  {
    title: '记录模型评估',
    description: '沉淀 Precision、Recall、mAP、F1 与样本数量，便于医生侧解释模型能力边界。',
  },
]

function resetForm() {
  form.name = ''
  form.source_name = ''
  form.homepage_url = ''
  form.paper_url = ''
  form.license = ''
  form.image_type = 'panoramic'
  form.task_types = []
  form.disease_tags = []
  form.sample_size = ''
  form.annotation_format = ''
  form.access_status = 'open'
  form.priority = 'medium'
  form.notes = ''
}

function openCreateDialog() {
  editingDataset.value = null
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(dataset: DatasetCatalog) {
  editingDataset.value = dataset
  form.name = dataset.name
  form.source_name = dataset.source_name
  form.homepage_url = dataset.homepage_url
  form.paper_url = dataset.paper_url ?? ''
  form.license = dataset.license ?? ''
  form.image_type = dataset.image_type
  form.task_types = [...dataset.task_types]
  form.disease_tags = [...dataset.disease_tags]
  form.sample_size = dataset.sample_size ?? ''
  form.annotation_format = dataset.annotation_format ?? ''
  form.access_status = dataset.access_status
  form.priority = dataset.priority
  form.notes = dataset.notes ?? ''
  dialogVisible.value = true
}

function openDetail(dataset: DatasetCatalog) {
  selectedDataset.value = dataset
  detailVisible.value = true
}

async function selectDataset(dataset: DatasetCatalog) {
  selectedDataset.value = dataset
  importsPagination.value = { ...importsPagination.value, offset: 0 }
  evaluationsPagination.value = { ...evaluationsPagination.value, offset: 0 }
  await Promise.all([refreshImports(), refreshEvaluations()])
}

async function refreshDatasets() {
  if (!canReadImages.value) {
    datasets.value = []
    return
  }
  loading.value = true
  try {
    const result = await listDatasets(filters, {
      limit: pagination.value.limit,
      offset: pagination.value.offset,
    })
    datasets.value = result.items
    pagination.value = result.meta
    if (!selectedDataset.value && result.items.length > 0) {
      selectedDataset.value = result.items[0]
      await Promise.all([refreshImports(), refreshEvaluations()])
    }
  } finally {
    loading.value = false
  }
}

async function refreshImports() {
  if (!selectedDataset.value || !canReadImages.value) {
    imports.value = []
    return
  }
  importsLoading.value = true
  try {
    const result = await listDatasetImports(selectedDataset.value.dataset_id, {
      limit: importsPagination.value.limit,
      offset: importsPagination.value.offset,
    })
    imports.value = result.items
    importsPagination.value = result.meta
  } finally {
    importsLoading.value = false
  }
}

async function refreshSamples() {
  if (!selectedImport.value || !canReadImages.value) {
    samples.value = []
    return
  }
  samplesLoading.value = true
  try {
    const result = await listDatasetSamples(selectedImport.value.import_id, {
      limit: samplesPagination.value.limit,
      offset: samplesPagination.value.offset,
    })
    samples.value = result.items
    samplesPagination.value = result.meta
  } finally {
    samplesLoading.value = false
  }
}

async function refreshEvaluations() {
  if (!selectedDataset.value || !canReadImages.value) {
    evaluations.value = []
    return
  }
  const result = await listModelEvaluations(
    { dataset_id: selectedDataset.value.dataset_id },
    { limit: evaluationsPagination.value.limit, offset: evaluationsPagination.value.offset },
  )
  evaluations.value = result.items
  evaluationsPagination.value = result.meta
}

async function applyFilters() {
  pagination.value = { ...pagination.value, offset: 0 }
  await refreshDatasets()
}

async function resetFilters() {
  filters.keyword = ''
  filters.task_type = ''
  filters.disease = ''
  await applyFilters()
}

async function handlePageChange(page: number) {
  pagination.value = { ...pagination.value, offset: (page - 1) * pagination.value.limit }
  await refreshDatasets()
}

async function handleSeedPublicDatasets() {
  if (!canUpload.value) {
    ElMessage.warning('初始化公开数据集需要上传/维护权限')
    return
  }
  const result = await seedPublicDatasets()
  ElMessage.success(`公开数据集已同步：新增 ${result.created}，跳过 ${result.skipped}`)
  await refreshDatasets()
  await refreshDashboardSummary()
}

async function submitDataset() {
  if (!form.name || !form.source_name || !form.homepage_url) {
    ElMessage.warning('请填写数据集名称、来源和主页 URL')
    return
  }
  const payload = {
    ...form,
    paper_url: form.paper_url || null,
    license: form.license || null,
    sample_size: form.sample_size || null,
    annotation_format: form.annotation_format || null,
    notes: form.notes || null,
  }
  if (editingDataset.value) {
    await updateDataset(editingDataset.value.dataset_id, payload)
    ElMessage.success('数据集登记已更新')
  } else {
    await createDataset(payload)
    ElMessage.success('数据集登记已创建')
  }
  dialogVisible.value = false
  await refreshDatasets()
  await refreshDashboardSummary()
}

function openImportDialog() {
  if (!selectedDataset.value) {
    ElMessage.warning('请先选择数据集')
    return
  }
  importForm.import_method = 'local_directory'
  importForm.source_path = ''
  importForm.sample_count = 0
  importForm.annotation_format = selectedDataset.value.annotation_format ?? ''
  importForm.image_type = selectedDataset.value.image_type
  importForm.notes = ''
  zipFile.value = null
  importDialogVisible.value = true
}

function openEvaluationDialog() {
  if (!selectedDataset.value) {
    ElMessage.warning('请先选择数据集')
    return
  }
  evaluationForm.model_name = ''
  evaluationForm.model_version = ''
  evaluationForm.dataset_id = selectedDataset.value.dataset_id
  evaluationForm.import_id = selectedImport.value?.import_id ?? null
  evaluationForm.precision = null
  evaluationForm.recall = null
  evaluationForm.map_score = null
  evaluationForm.f1_score = null
  evaluationForm.sample_count = selectedImport.value?.sample_count ?? null
  evaluationForm.notes = ''
  evaluationDialogVisible.value = true
}

function handleZipChange(file: { raw?: File }) {
  zipFile.value = file.raw ?? null
}

async function submitImport() {
  if (!selectedDataset.value) {
    return
  }
  if (importForm.import_method === 'zip_upload' && !zipFile.value) {
    ElMessage.warning('请先选择 zip 样本包')
    return
  }
  if (importForm.import_method === 'url_download' && !importForm.source_path) {
    ElMessage.warning('请填写可直接下载的 zip URL')
    return
  }
  const selectedZipFile = zipFile.value
  const sourceUrl = importForm.source_path || ''
  if (importForm.import_method === 'url_download') {
    await downloadDatasetZip(selectedDataset.value.dataset_id, {
      source_url: sourceUrl,
      sample_count: importForm.sample_count,
      annotation_format: importForm.annotation_format || null,
      image_type: importForm.image_type,
      notes: importForm.notes || null,
    })
  } else {
    const created = await createDatasetImport(selectedDataset.value.dataset_id, {
      ...importForm,
      source_path: importForm.source_path || null,
      annotation_format: importForm.annotation_format || null,
      notes: importForm.notes || null,
    })
    if (importForm.import_method === 'zip_upload' && selectedZipFile) {
      await uploadDatasetZip(created.import_id, selectedZipFile)
    }
  }
  ElMessage.success('导入批次已创建')
  importDialogVisible.value = false
  await refreshImports()
}

async function openSamplesDrawer(item: DatasetImportRecord) {
  selectedImport.value = item
  samplesPagination.value = { ...samplesPagination.value, offset: 0 }
  samplesDrawerVisible.value = true
  await refreshSamples()
}

async function handleSplitImport(item: DatasetImportRecord) {
  const result = await splitDatasetImport(item.import_id, { train_ratio: 0.7, val_ratio: 0.15, test_ratio: 0.15 })
  ElMessage.success(`划分完成：train ${result.train} / val ${result.val} / test ${result.test}`)
  await refreshImports()
  if (selectedImport.value?.import_id === item.import_id) {
    await refreshSamples()
  }
}

async function submitEvaluation() {
  if (!evaluationForm.model_name || !evaluationForm.model_version) {
    ElMessage.warning('请填写模型名称和版本')
    return
  }
  await createModelEvaluation({
    ...evaluationForm,
    dataset_id: evaluationForm.dataset_id || null,
    import_id: evaluationForm.import_id || null,
    notes: evaluationForm.notes || null,
  })
  ElMessage.success('模型评估记录已创建')
  evaluationDialogVisible.value = false
  await refreshEvaluations()
}

function getPriorityTagType(priority: string) {
  if (priority === 'high') {
    return 'danger'
  }
  if (priority === 'medium') {
    return 'warning'
  }
  return 'info'
}

function getAccessStatusLabel(status: string) {
  const labels: Record<string, string> = {
    open: '开放',
    open_reference: '公开索引',
    open_registration: '注册访问',
    application_required: '需申请',
    restricted: '受限',
  }
  return labels[status] ?? status
}

watch(canReadImages, async (value) => {
  if (value) {
    await refreshDatasets()
  }
})

onMounted(async () => {
  if (canReadImages.value) {
    await refreshDatasets()
  }
})
</script>

<template>
  <div class="page-stack">
    <section class="medical-page-header compact-page-header dataset-intro">
      <div>
        <div class="overview-pill">数据集中心</div>
        <h2>把公开牙科影像变成可训练的数据底座。</h2>
        <p>围绕儿童牙科全景片、YOLO 标注、样本索引、训练集划分和模型评估，保持数据准备流程可追踪。</p>
      </div>
    </section>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !canReadImages"
      title="当前账号暂无数据集中心访问权限"
      description="数据集目录读取沿用 `read:images` 权限，请为当前用户分配可查看影像的角色。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <template v-else>
      <section class="dataset-dashboard-grid">
        <div class="dataset-kpi-grid">
          <div class="dataset-kpi-card">
            <strong>{{ pagination.total }}</strong>
            <span>已登记数据集</span>
          </div>
          <div class="dataset-kpi-card">
            <strong>{{ openDatasetCount }}</strong>
            <span>可访问公开来源</span>
          </div>
          <div class="dataset-kpi-card">
            <strong>{{ totalDiseaseTags }}</strong>
            <span>病种/标签覆盖</span>
          </div>
          <div class="dataset-kpi-card">
            <strong>{{ highPriorityDatasetCount }}</strong>
            <span>高优先级训练来源</span>
          </div>
        </div>

        <article class="dataset-focus-panel">
          <div class="overview-pill">参考重点</div>
          <h3>{{ featuredDataset?.name ?? '儿童牙科全景片数据集' }}</h3>
          <p>
            以儿童牙科全景 X 光数据、YOLO 标注和 14 类标签为重点参考，服务龋齿检测、儿童口腔疾病识别和 YOLOv8-C2f-CBAM 实验评估。
          </p>
          <div class="dataset-focus-metrics">
            <div>
              <strong>1164</strong>
              <span>全景片参考规模</span>
            </div>
            <div>
              <strong>YOLO</strong>
              <span>标注格式</span>
            </div>
            <div>
              <strong>14 类</strong>
              <span>病灶/牙体标签</span>
            </div>
          </div>
        </article>
      </section>

      <section class="dataset-ops-grid">
        <el-card class="panel" shadow="never">
          <template #header>
            <div class="panel-header">
              <span>公开数据来源</span>
              <div class="quick-action-row">
                <el-tooltip v-if="!canUpload" content="需要 upload:images 权限" placement="top">
                  <span><el-button type="primary" disabled>初始化公开清单</el-button></span>
                </el-tooltip>
                <el-button v-else type="primary" @click="handleSeedPublicDatasets">初始化公开清单</el-button>
                <el-button v-if="canUpload" plain @click="openCreateDialog">新增登记</el-button>
              </div>
            </div>
          </template>

          <details class="compact-details">
            <summary>搜索和筛选</summary>
            <div class="dataset-filter-row">
              <el-input v-model="filters.keyword" placeholder="搜索名称、来源或备注" clearable @keyup.enter="applyFilters" />
              <el-input v-model="filters.task_type" placeholder="任务类型，如 segmentation" clearable @keyup.enter="applyFilters" />
              <el-input v-model="filters.disease" placeholder="病种标签，如 caries" clearable @keyup.enter="applyFilters" />
              <el-button type="primary" @click="applyFilters">筛选</el-button>
              <el-button @click="resetFilters">重置</el-button>
            </div>
          </details>

          <el-skeleton v-if="loading" :rows="6" animated />
          <div v-else-if="datasets.length === 0" class="empty-action-card">
            <strong>还没有公开数据集登记</strong>
            <p>点击“初始化公开清单”写入儿童牙科全景片、DENTEX、OdontoAI、Tufts、Mendeley 等推荐来源。</p>
            <el-tooltip v-if="!canUpload" content="需要 upload:images 权限" placement="top">
              <span><el-button type="primary" disabled>初始化公开清单</el-button></span>
            </el-tooltip>
            <el-button v-else type="primary" @click="handleSeedPublicDatasets">初始化公开清单</el-button>
          </div>
          <div v-else class="dataset-card-grid">
            <article
              v-for="dataset in datasets"
              :key="dataset.dataset_id"
              class="dataset-card"
              :class="{ active: selectedDataset?.dataset_id === dataset.dataset_id }"
            >
              <div class="panel-header">
                <strong>{{ dataset.name }}</strong>
                <el-tag :type="getPriorityTagType(dataset.priority)">{{ dataset.priority }}</el-tag>
              </div>
              <p>{{ dataset.notes || '暂无备注' }}</p>
              <div class="record-meta dataset-primary-meta">
                <el-tag>{{ dataset.image_type }}</el-tag>
                <el-tag type="success">{{ getAccessStatusLabel(dataset.access_status) }}</el-tag>
                <el-tag v-if="dataset.license" type="info">{{ dataset.license }}</el-tag>
              </div>
              <div class="dataset-tag-list compact-tag-list">
                <el-tag v-for="task in dataset.task_types" :key="`${dataset.dataset_id}-${task}`" size="small">{{ task }}</el-tag>
                <el-tag v-for="disease in dataset.disease_tags" :key="`${dataset.dataset_id}-${disease}`" size="small" type="warning">{{ disease }}</el-tag>
              </div>
              <div class="quick-action-row">
                <el-button type="primary" @click="selectDataset(dataset)">选择</el-button>
                <el-button type="primary" plain @click="openDetail(dataset)">详情</el-button>
                <el-button v-if="canUpload" text @click="openEditDialog(dataset)">编辑</el-button>
                <a :href="dataset.homepage_url" target="_blank" rel="noreferrer" class="el-button is-text">访问来源</a>
              </div>
            </article>
          </div>

          <div class="pagination-row">
            <el-pagination
              background
              layout="total, prev, pager, next"
              :current-page="Math.floor(pagination.offset / pagination.limit) + 1"
              :page-size="pagination.limit"
              :total="pagination.total"
              @current-change="handlePageChange"
            />
          </div>
        </el-card>

        <el-card class="panel" shadow="never">
          <template #header>
            <div class="panel-header">
              <span>数据准备闭环</span>
              <el-tag type="success">功能流程</el-tag>
            </div>
          </template>
          <div class="dataset-pipeline">
            <div v-for="(step, index) in datasetPipelineSteps" :key="step.title" class="dataset-pipeline-step">
              <span>{{ index + 1 }}</span>
              <div>
                <strong>{{ step.title }}</strong>
                <small>{{ step.description }}</small>
              </div>
            </div>
          </div>
        </el-card>
      </section>

      <el-card v-if="selectedDataset" class="panel dataset-workbench-panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>数据准备工作区：{{ selectedDataset.name }}</span>
            <div class="quick-action-row">
              <el-button v-if="canUpload" type="primary" plain @click="openImportDialog">新建导入</el-button>
              <el-button v-if="canUpload" plain @click="openEvaluationDialog">新增评估</el-button>
            </div>
          </div>
        </template>

        <div class="dataset-brief-row dataset-status-row">
          <span v-for="item in selectedDatasetMetrics" :key="item.label">{{ item.label }} {{ item.value }}</span>
          <span>{{ selectedDataset.annotation_format || '标注格式未填' }}</span>
          <span>{{ getAccessStatusLabel(selectedDataset.access_status) }}</span>
        </div>

        <el-tabs v-model="activeDatasetTab" class="dataset-tabs">
          <el-tab-pane label="导入批次" name="imports">
            <div class="dataset-tab-note">记录本地目录、ZIP 样本包、公开 ZIP 直链或手动统计，后续训练前先确认样本索引。</div>
            <el-skeleton v-if="importsLoading" :rows="4" animated />
            <el-empty v-else-if="imports.length === 0" description="暂无导入批次，可登记本地目录、手动统计或上传 zip" />
            <el-table v-else :data="imports" stripe>
              <el-table-column prop="import_method" label="方式" min-width="120" />
              <el-table-column prop="sample_count" label="样本" min-width="80" />
              <el-table-column prop="status" label="状态" min-width="100" />
              <el-table-column prop="annotation_format" label="标注格式" min-width="120" />
              <el-table-column label="操作" width="240">
                <template #default="scope">
                  <el-button text @click="openSamplesDrawer(scope.row)">样本</el-button>
                  <el-button text :disabled="!canUpload" @click="handleSplitImport(scope.row)">70/15/15 划分</el-button>
                  <el-button text :disabled="!canUpload" @click="selectedImport = scope.row; openEvaluationDialog()">评估</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="模型评估" name="evaluations">
            <div class="dataset-tab-note">只记录评估结果和备注，不在这里训练模型。</div>
            <el-empty v-if="evaluations.length === 0" description="暂无模型评估记录" />
            <el-table v-else :data="evaluations" stripe>
              <el-table-column prop="model_name" label="模型" min-width="130" />
              <el-table-column prop="model_version" label="版本" min-width="100" />
              <el-table-column label="mAP" min-width="80">
                <template #default="scope">{{ scope.row.map_score ?? '-' }}</template>
              </el-table-column>
              <el-table-column label="F1" min-width="80">
                <template #default="scope">{{ scope.row.f1_score ?? '-' }}</template>
              </el-table-column>
              <el-table-column prop="sample_count" label="样本" min-width="80" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </template>

    <el-drawer v-model="detailVisible" title="数据集详情" size="520px">
      <el-empty v-if="!selectedDataset" description="请选择数据集" />
      <div v-else class="dataset-detail-stack">
        <h3>{{ selectedDataset.name }}</h3>
        <div class="patient-note-box">
          <strong>来源</strong>
          <span>{{ selectedDataset.source_name }}</span>
          <strong>主页</strong>
          <a :href="selectedDataset.homepage_url" target="_blank" rel="noreferrer">{{ selectedDataset.homepage_url }}</a>
          <strong>论文/DOI</strong>
          <a v-if="selectedDataset.paper_url" :href="selectedDataset.paper_url" target="_blank" rel="noreferrer">{{ selectedDataset.paper_url }}</a>
          <span v-else>未填写</span>
          <strong>样本规模</strong>
          <span>{{ selectedDataset.sample_size || '未填写' }}</span>
          <strong>标注格式</strong>
          <span>{{ selectedDataset.annotation_format || '未填写' }}</span>
          <strong>许可</strong>
          <span>{{ selectedDataset.license || '未填写' }}</span>
          <strong>备注</strong>
          <span>{{ selectedDataset.notes || '暂无备注' }}</span>
        </div>
        <div class="dataset-tag-list">
          <el-tag v-for="task in selectedDataset.task_types" :key="task">{{ task }}</el-tag>
          <el-tag v-for="disease in selectedDataset.disease_tags" :key="disease" type="warning">{{ disease }}</el-tag>
        </div>
      </div>
    </el-drawer>

    <el-drawer v-model="samplesDrawerVisible" title="样本索引" size="680px">
      <el-empty v-if="!selectedImport" description="请选择导入批次" />
      <template v-else>
        <div class="dataset-brief-row">
          <span>{{ selectedImport.import_method }}</span>
          <span>{{ selectedImport.sample_count }} 个样本</span>
          <span>{{ selectedImport.status }}</span>
        </div>
        <el-skeleton v-if="samplesLoading" :rows="5" animated />
        <el-table v-else :data="samples" stripe>
          <el-table-column prop="filename" label="文件名" min-width="240" />
          <el-table-column prop="file_type" label="类型" min-width="90" />
          <el-table-column prop="annotation_status" label="标注" min-width="100" />
          <el-table-column prop="split" label="划分" min-width="80" />
        </el-table>
        <div class="pagination-row">
          <el-pagination
            background
            layout="total, prev, pager, next"
            :current-page="Math.floor(samplesPagination.offset / samplesPagination.limit) + 1"
            :page-size="samplesPagination.limit"
            :total="samplesPagination.total"
            @current-change="async (page: number) => { samplesPagination.offset = (page - 1) * samplesPagination.limit; await refreshSamples() }"
          />
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="dialogVisible" :title="editingDataset ? '编辑数据集登记' : '新增数据集登记'" width="680px">
      <el-form label-position="top">
        <el-form-item label="数据集名称">
          <el-input v-model="form.name" placeholder="例如 DENTEX 2023 Challenge" />
        </el-form-item>
        <div class="dialog-form-grid">
          <el-form-item label="来源">
            <el-input v-model="form.source_name" placeholder="例如 Grand Challenge / Zenodo" />
          </el-form-item>
          <el-form-item label="影像类型">
            <el-select v-model="form.image_type" class="w-full">
              <el-option label="全景片 panoramic" value="panoramic" />
              <el-option label="根尖片 periapical" value="periapical" />
              <el-option label="CBCT" value="cbct" />
              <el-option label="混合 mixed" value="mixed" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="主页 URL">
          <el-input v-model="form.homepage_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="论文 / DOI URL">
          <el-input v-model="form.paper_url" placeholder="可选" />
        </el-form-item>
        <div class="dialog-form-grid">
          <el-form-item label="许可">
            <el-input v-model="form.license" placeholder="例如 CC BY 4.0" />
          </el-form-item>
          <el-form-item label="访问状态">
            <el-select v-model="form.access_status" class="w-full">
              <el-option label="开放" value="open" />
              <el-option label="公开索引" value="open_reference" />
              <el-option label="注册访问" value="open_registration" />
              <el-option label="需申请" value="application_required" />
              <el-option label="受限" value="restricted" />
            </el-select>
          </el-form-item>
        </div>
        <div class="dialog-form-grid">
          <el-form-item label="样本规模">
            <el-input v-model="form.sample_size" placeholder="例如 1000 panoramic radiographs" />
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="form.priority" class="w-full">
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="任务类型">
          <el-select v-model="form.task_types" class="w-full" multiple filterable allow-create default-first-option>
            <el-option label="disease detection" value="disease detection" />
            <el-option label="caries segmentation" value="caries segmentation" />
            <el-option label="tooth segmentation" value="tooth segmentation" />
            <el-option label="tooth numbering" value="tooth numbering" />
          </el-select>
        </el-form-item>
        <el-form-item label="病种/标签">
          <el-select v-model="form.disease_tags" class="w-full" multiple filterable allow-create default-first-option>
            <el-option label="caries" value="caries" />
            <el-option label="deep caries" value="deep caries" />
            <el-option label="periapical lesions" value="periapical lesions" />
            <el-option label="impacted teeth" value="impacted teeth" />
          </el-select>
        </el-form-item>
        <el-form-item label="标注格式">
          <el-input v-model="form.annotation_format" placeholder="例如 COCO / masks / labels" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="许可注意事项、使用建议、适配模型等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!canUpload" @click="submitDataset">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="新建数据导入批次" width="620px">
      <el-form label-position="top">
        <el-form-item label="导入方式">
          <el-select v-model="importForm.import_method" class="w-full">
            <el-option label="本地目录登记" value="local_directory" />
            <el-option label="ZIP 样本包上传" value="zip_upload" />
            <el-option label="公开 ZIP 直链下载" value="url_download" />
            <el-option label="手动统计录入" value="manual_summary" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="importForm.import_method !== 'manual_summary'" label="来源路径 / 说明">
          <el-input
            v-model="importForm.source_path"
            :placeholder="importForm.import_method === 'url_download' ? 'https://example.com/dataset.zip' : 'Docker 中建议填写 /datasets/x 或 /datasets/dental_xray'"
          />
          <div v-if="importForm.import_method === 'url_download'" class="dataset-tab-note">
            请输入可匿名直接下载的 zip 文件地址；Kaggle 页面地址通常不是 zip 直链。
          </div>
        </el-form-item>
        <el-form-item v-if="importForm.import_method === 'zip_upload'" label="ZIP 样本包">
          <el-upload :auto-upload="false" :limit="1" :on-change="handleZipChange">
            <el-button type="primary" plain>选择 zip</el-button>
          </el-upload>
        </el-form-item>
        <div class="dialog-form-grid">
          <el-form-item label="样本数量">
            <el-input-number v-model="importForm.sample_count" class="w-full" :min="0" controls-position="right" />
          </el-form-item>
          <el-form-item label="影像类型">
            <el-select v-model="importForm.image_type" class="w-full">
              <el-option label="全景片" value="panoramic" />
              <el-option label="根尖片" value="periapical" />
              <el-option label="CBCT" value="cbct" />
              <el-option label="混合" value="mixed" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="标注格式">
          <el-input v-model="importForm.annotation_format" placeholder="例如 COCO / masks / labels" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="importForm.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!canUpload" @click="submitImport">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="evaluationDialogVisible" title="新增模型评估记录" width="620px">
      <el-form label-position="top">
        <div class="dialog-form-grid">
          <el-form-item label="模型名称">
            <el-input v-model="evaluationForm.model_name" placeholder="例如 YOLOv8 Dental Baseline" />
          </el-form-item>
          <el-form-item label="模型版本">
            <el-input v-model="evaluationForm.model_version" placeholder="例如 v0.1" />
          </el-form-item>
        </div>
        <div class="dialog-form-grid">
          <el-form-item label="Precision">
            <el-input-number v-model="evaluationForm.precision" class="w-full" :min="0" :max="1" :step="0.01" />
          </el-form-item>
          <el-form-item label="Recall">
            <el-input-number v-model="evaluationForm.recall" class="w-full" :min="0" :max="1" :step="0.01" />
          </el-form-item>
        </div>
        <div class="dialog-form-grid">
          <el-form-item label="mAP">
            <el-input-number v-model="evaluationForm.map_score" class="w-full" :min="0" :max="1" :step="0.01" />
          </el-form-item>
          <el-form-item label="F1">
            <el-input-number v-model="evaluationForm.f1_score" class="w-full" :min="0" :max="1" :step="0.01" />
          </el-form-item>
        </div>
        <el-form-item label="样本数量">
          <el-input-number v-model="evaluationForm.sample_count" class="w-full" :min="0" controls-position="right" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="evaluationForm.notes" type="textarea" :rows="3" placeholder="评估集、训练设置、失败原因等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="evaluationDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!canUpload" @click="submitEvaluation">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
