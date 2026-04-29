<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { createDataset, listDatasets, seedPublicDatasets, updateDataset } from '../api/datasets'
import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import type { PaginationMeta } from '../types/analysis'
import type { DatasetCatalog, DatasetCatalogPayload } from '../types/dataset'
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
const loading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const editingDataset = ref<DatasetCatalog | null>(null)
const filters = reactive({
  keyword: '',
  task_type: '',
  disease: '',
})
const pagination = ref<PaginationMeta>({ limit: 9, offset: 0, total: 0 })
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

const totalDiseaseTags = computed(() => new Set(datasets.value.flatMap((item) => item.disease_tags)).size)
const openDatasetCount = computed(() => datasets.value.filter((item) => ['open', 'open_reference', 'open_registration'].includes(item.access_status)).length)

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
  } finally {
    loading.value = false
  }
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
    <section class="medical-page-header compact-page-header">
      <div>
        <div class="overview-pill">数据集中心</div>
        <h2>为模型训练准备公开数据来源</h2>
        <p>先登记来源和许可，不下载真实影像。推荐从 DENTEX、OdontoAI 和 Tufts 开始。</p>
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
      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>推荐公开清单</span>
            <div class="quick-action-row">
              <el-tooltip v-if="!canUpload" content="需要 upload:images 权限" placement="top">
                <span><el-button type="primary" disabled>初始化公开清单</el-button></span>
              </el-tooltip>
              <el-button v-else type="primary" @click="handleSeedPublicDatasets">初始化公开清单</el-button>
              <el-button v-if="canUpload" plain @click="openCreateDialog">新增登记</el-button>
            </div>
          </div>
        </template>

        <div class="dataset-brief-row">
          <span>{{ pagination.total }} 个数据集</span>
          <span>{{ openDatasetCount }} 个可访问来源</span>
          <span>{{ totalDiseaseTags }} 类标签</span>
        </div>

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
          <p>点击“初始化公开清单”写入 DENTEX、OdontoAI、Tufts、Mendeley 等推荐来源。</p>
          <el-tooltip v-if="!canUpload" content="需要 upload:images 权限" placement="top">
            <span><el-button type="primary" disabled>初始化公开清单</el-button></span>
          </el-tooltip>
          <el-button v-else type="primary" @click="handleSeedPublicDatasets">初始化公开清单</el-button>
        </div>
        <div v-else class="dataset-card-grid">
          <article v-for="dataset in datasets" :key="dataset.dataset_id" class="dataset-card">
            <div class="panel-header">
              <strong>{{ dataset.name }}</strong>
              <el-tag :type="getPriorityTagType(dataset.priority)">{{ dataset.priority }}</el-tag>
            </div>
            <p>{{ dataset.notes || '暂无备注' }}</p>
            <div class="record-meta">
              <el-tag>{{ dataset.image_type }}</el-tag>
              <el-tag type="success">{{ getAccessStatusLabel(dataset.access_status) }}</el-tag>
              <el-tag v-if="dataset.license" type="info">{{ dataset.license }}</el-tag>
            </div>
            <div class="dataset-tag-list">
              <el-tag v-for="task in dataset.task_types" :key="`${dataset.dataset_id}-${task}`" size="small">{{ task }}</el-tag>
              <el-tag v-for="disease in dataset.disease_tags" :key="`${dataset.dataset_id}-${disease}`" size="small" type="warning">{{ disease }}</el-tag>
            </div>
            <div class="quick-action-row">
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
  </div>
</template>
