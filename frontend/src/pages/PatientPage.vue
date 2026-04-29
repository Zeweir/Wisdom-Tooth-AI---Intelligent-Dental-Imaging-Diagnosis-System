<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { createPatient, listPatientImages, listPatients, updatePatient } from '../api/patients'
import UnauthorizedPanel from '../components/UnauthorizedPanel.vue'
import type { AnalysisItem, PaginationMeta } from '../types/analysis'
import type { PatientFormPayload, PatientRecord } from '../types/patient'
import { getImageTypeLabel, getReportStatusLabel, getReportStatusTagType } from '../utils/display'
import { useWorkbenchContext } from '../workbench'

const workbench = useWorkbenchContext()
const isAuthenticated = workbench.isAuthenticated
const authReady = workbench.authReady
const canReadImages = workbench.canReadImages
const canUpload = workbench.canUpload
const beginSignOut = workbench.beginSignOut

const patients = ref<PatientRecord[]>([])
const selectedPatientId = ref('')
const patientImages = ref<AnalysisItem[]>([])
const loading = ref(false)
const imagesLoading = ref(false)
const keyword = ref('')
const dialogVisible = ref(false)
const editingPatient = ref<PatientRecord | null>(null)
const pagination = ref<PaginationMeta>({ limit: 10, offset: 0, total: 0 })
const imagePagination = ref<PaginationMeta>({ limit: 6, offset: 0, total: 0 })

const form = reactive<PatientFormPayload>({
  patient_id: '',
  name: '',
  gender: '',
  age: null,
  phone: '',
  notes: '',
})

const selectedPatient = computed(() => patients.value.find((item) => item.patient_id === selectedPatientId.value) ?? null)
const patientTitle = computed(() => selectedPatient.value ? `${selectedPatient.value.name} (${selectedPatient.value.patient_id})` : '选择患者查看病例')
const latestImageLabel = computed(() => selectedPatient.value?.latest_image_at ? new Date(selectedPatient.value.latest_image_at).toLocaleString() : '暂无影像')

function resetForm() {
  form.patient_id = ''
  form.name = ''
  form.gender = ''
  form.age = null
  form.phone = ''
  form.notes = ''
}

function openCreateDialog() {
  editingPatient.value = null
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(patient: PatientRecord) {
  editingPatient.value = patient
  form.patient_id = patient.patient_id
  form.name = patient.name
  form.gender = patient.gender ?? ''
  form.age = patient.age
  form.phone = patient.phone ?? ''
  form.notes = patient.notes ?? ''
  dialogVisible.value = true
}

async function refreshPatients() {
  if (!canReadImages.value) {
    patients.value = []
    selectedPatientId.value = ''
    return
  }
  loading.value = true
  try {
    const result = await listPatients(keyword.value, {
      limit: pagination.value.limit,
      offset: pagination.value.offset,
    })
    patients.value = result.items
    pagination.value = result.meta
    if (selectedPatientId.value && !patients.value.some((item) => item.patient_id === selectedPatientId.value)) {
      selectedPatientId.value = ''
    }
    if (!selectedPatientId.value && patients.value.length > 0) {
      selectedPatientId.value = patients.value[0].patient_id
    }
  } finally {
    loading.value = false
  }
}

async function refreshPatientImages() {
  if (!selectedPatientId.value || !canReadImages.value) {
    patientImages.value = []
    return
  }
  imagesLoading.value = true
  try {
    const result = await listPatientImages(selectedPatientId.value, {
      limit: imagePagination.value.limit,
      offset: imagePagination.value.offset,
    })
    patientImages.value = result.items
    imagePagination.value = result.meta
  } finally {
    imagesLoading.value = false
  }
}

async function selectPatient(patientId: string) {
  selectedPatientId.value = patientId
  imagePagination.value = { ...imagePagination.value, offset: 0 }
  await refreshPatientImages()
}

async function applySearch() {
  pagination.value = { ...pagination.value, offset: 0 }
  await refreshPatients()
  await refreshPatientImages()
}

async function handlePageChange(page: number) {
  pagination.value = { ...pagination.value, offset: (page - 1) * pagination.value.limit }
  await refreshPatients()
}

async function handlePatientImagesPageChange(page: number) {
  imagePagination.value = { ...imagePagination.value, offset: (page - 1) * imagePagination.value.limit }
  await refreshPatientImages()
}

async function submitPatient() {
  if (!form.patient_id || !form.name) {
    ElMessage.warning('请填写患者编号和姓名')
    return
  }
  const payload = {
    name: form.name,
    gender: form.gender || null,
    age: form.age ?? null,
    phone: form.phone || null,
    notes: form.notes || null,
  }
  if (editingPatient.value) {
    await updatePatient(editingPatient.value.patient_id, payload)
    ElMessage.success('患者档案已更新')
  } else {
    await createPatient({ patient_id: form.patient_id, ...payload })
    ElMessage.success('患者档案已创建')
  }
  dialogVisible.value = false
  await refreshPatients()
  selectedPatientId.value = form.patient_id
  await refreshPatientImages()
}

watch(selectedPatientId, async () => {
  await refreshPatientImages()
})

watch(canReadImages, async (value) => {
  if (value) {
    await refreshPatients()
  }
})

onMounted(async () => {
  if (canReadImages.value) {
    await refreshPatients()
    await refreshPatientImages()
  }
})
</script>

<template>
  <div class="page-stack">
    <section class="medical-page-header">
      <div>
        <div class="overview-pill">患者档案</div>
        <h2>先找到患者，再查看历史病例。</h2>
        <p>患者页只做两件事：维护基础档案，快速回到对应影像报告。</p>
      </div>
    </section>

    <UnauthorizedPanel
      v-if="isAuthenticated && authReady && !canReadImages"
      title="当前账号暂无患者档案访问权限"
      description="患者档案读取沿用 `read:images` 权限，请为当前用户分配可查看影像的角色。"
    >
      <el-button @click="beginSignOut">退出当前账号</el-button>
    </UnauthorizedPanel>

    <section v-else class="patient-workspace-grid">
      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>患者</span>
            <el-button v-if="canUpload" type="primary" plain @click="openCreateDialog">新建患者</el-button>
          </div>
        </template>

        <div class="patient-search-row">
          <el-input v-model="keyword" placeholder="搜索患者编号或姓名" clearable @keyup.enter="applySearch" />
          <el-button type="primary" @click="applySearch">搜索</el-button>
        </div>

        <el-skeleton v-if="loading" :rows="5" animated />
        <el-empty v-else-if="patients.length === 0" description="暂无患者档案" />
        <div v-else class="record-list patient-list">
          <button
            v-for="patient in patients"
            :key="patient.patient_id"
            class="record-item"
            :class="{ active: selectedPatientId === patient.patient_id }"
            @click="selectPatient(patient.patient_id)"
          >
            <div class="record-main">
              <strong>{{ patient.name }}</strong>
              <span>{{ patient.patient_id }}</span>
            </div>
            <div class="record-meta">
              <el-tag size="small">{{ patient.gender || '性别未填' }}</el-tag>
              <el-tag size="small" type="success">{{ patient.image_count }} 条影像</el-tag>
            </div>
          </button>
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

      <div class="workbench-column">
        <el-card class="panel" shadow="never">
          <template #header>
            <div class="panel-header">
              <span>{{ patientTitle }}</span>
              <el-button v-if="canUpload && selectedPatient" text @click="openEditDialog(selectedPatient)">编辑</el-button>
            </div>
          </template>

          <el-empty v-if="!selectedPatient" description="请选择患者" />
          <template v-else>
            <div class="patient-summary-grid">
              <div class="clinical-metric">
                <div class="metric-value">{{ selectedPatient.image_count }}</div>
                <div class="metric-label">历史影像</div>
              </div>
              <div class="clinical-metric">
                <div class="metric-value">{{ selectedPatient.age ?? '-' }}</div>
                <div class="metric-label">年龄</div>
              </div>
              <div class="clinical-metric">
                <div class="metric-value">{{ selectedPatient.gender || '-' }}</div>
                <div class="metric-label">性别</div>
              </div>
            </div>
            <div class="patient-note-box">
              <strong>联系方式</strong>
              <span>{{ selectedPatient.phone || '未填写' }}</span>
              <strong>最近影像</strong>
              <span>{{ latestImageLabel }}</span>
              <strong>备注</strong>
              <span>{{ selectedPatient.notes || '暂无备注' }}</span>
            </div>
          </template>
        </el-card>

        <el-card class="panel" shadow="never">
          <template #header>
            <div class="panel-header">
              <span>历史病例</span>
              <el-tag v-if="selectedPatient" type="info">{{ patientImages.length }} 条</el-tag>
            </div>
          </template>

          <el-skeleton v-if="imagesLoading" :rows="4" animated />
          <el-empty v-else-if="patientImages.length === 0" description="暂无历史影像" />
          <div v-else class="patient-timeline">
            <div v-for="image in patientImages" :key="image.image_id" class="audit-card">
              <div class="audit-card-header">
                <div class="audit-main">
                  <strong>{{ getImageTypeLabel(image.image_type) }}</strong>
                  <div class="audit-detail">{{ image.filename }}</div>
                </div>
                <el-tag :type="getReportStatusTagType(image.report.status)">{{ getReportStatusLabel(image.report.status) }}</el-tag>
              </div>
              <div class="record-meta">
                <span class="timeline-meta-text">{{ image.detections.length }} 个病灶 / {{ new Date(image.created_at).toLocaleString() }}</span>
                <RouterLink
                  :to="{ path: '/workspace', query: { image_id: image.image_id } }"
                  class="el-button el-button--primary is-plain"
                >
                  <span>打开病例</span>
                </RouterLink>
              </div>
            </div>
          </div>

          <div class="pagination-row">
            <el-pagination
              background
              layout="total, prev, pager, next"
              :current-page="Math.floor(imagePagination.offset / imagePagination.limit) + 1"
              :page-size="imagePagination.limit"
              :total="imagePagination.total"
              @current-change="handlePatientImagesPageChange"
            />
          </div>
        </el-card>
      </div>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingPatient ? '编辑患者档案' : '新建患者档案'" width="520px">
      <el-form label-position="top">
        <el-form-item label="患者编号">
          <el-input v-model="form.patient_id" :disabled="Boolean(editingPatient)" placeholder="例如 P-0001" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.name" placeholder="患者姓名" />
        </el-form-item>
        <div class="dialog-form-grid">
          <el-form-item label="性别">
            <el-select v-model="form.gender" class="w-full" clearable>
              <el-option label="男" value="男" />
              <el-option label="女" value="女" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
          <el-form-item label="年龄">
            <el-input-number v-model="form.age" class="w-full" :min="0" :max="130" controls-position="right" />
          </el-form-item>
        </div>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" placeholder="可选" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="病史摘要、就诊说明等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!canUpload" @click="submitPatient">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
