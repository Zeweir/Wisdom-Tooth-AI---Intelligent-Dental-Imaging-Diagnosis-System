<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadUserFile } from 'element-plus'
import { listPatients } from '../api/patients'
import type { AnalysisItem } from '../types/analysis'
import type { PatientRecord } from '../types/patient'

const emit = defineEmits<{
  submit: [payload: { file: File; patientId: string; patientName?: string; imageType: AnalysisItem['image_type'] }]
}>()

const props = defineProps<{
  canUpload: boolean
}>()

const loading = defineModel<boolean>('loading', { required: true })
const socketEvents = defineModel<string[]>('socketEvents', { required: true })

const form = reactive({
  patientId: 'P-0001',
  patientName: '',
  imageType: 'panoramic' as AnalysisItem['image_type']
})
const uploadFile = ref<File | null>(null)
const uploadList = ref<UploadUserFile[]>([])
const patientOptions = ref<PatientRecord[]>([])
const patientsLoading = ref(false)
const previewUrl = ref('')

const fileMeta = computed(() => {
  if (!uploadFile.value) {
    return null
  }
  return {
    name: uploadFile.value.name,
    size: `${(uploadFile.value.size / 1024 / 1024).toFixed(2)} MB`,
    type: uploadFile.value.type || '未知类型',
    selectedAt: new Date().toLocaleString(),
  }
})

async function searchPatients(keyword = '') {
  if (!props.canUpload) {
    patientOptions.value = []
    return
  }
  patientsLoading.value = true
  try {
    const result = await listPatients(keyword, { limit: 8, offset: 0 })
    patientOptions.value = result.items
  } catch {
    patientOptions.value = []
  } finally {
    patientsLoading.value = false
  }
}

function handlePatientChange(patientId: string) {
  const patient = patientOptions.value.find((item) => item.patient_id === patientId)
  if (patient) {
    form.patientName = patient.name
  }
}

function handleFileChange(file: UploadUserFile) {
  uploadFile.value = file.raw ?? null
  uploadList.value = file ? [file] : []
  if (previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
  if (uploadFile.value && uploadFile.value.type.startsWith('image/')) {
    previewUrl.value = URL.createObjectURL(uploadFile.value)
  } else {
    previewUrl.value = ''
  }
}

function handleSubmit() {
  if (!uploadFile.value) {
    ElMessage.warning('请先选择影像文件')
    return
  }

  emit('submit', {
    file: uploadFile.value,
    patientId: form.patientId,
    patientName: form.patientName || undefined,
    imageType: form.imageType
  })
}

onMounted(() => {
  void searchPatients()
})

onBeforeUnmount(() => {
  if (previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
})
</script>

<template>
  <el-card class="panel upload-panel-v2" shadow="never">
    <template #header>
      <div class="panel-header">
        <span>影像上传</span>
        <el-tag>{{ form.imageType }}</el-tag>
      </div>
    </template>

    <el-form label-position="top" class="upload-form-v2">
      <div class="upload-dropzone-v2">
        <div class="upload-dropzone-head">
          <strong>拖拽或选择牙齿影像文件</strong>
          <el-tag type="success">支持 DICOM / PNG / JPG</el-tag>
        </div>
        <p class="upload-hint">建议上传脱敏后的口腔影像文件，上传成功后可直接进入 AI 诊断页面。</p>
        <el-upload
          drag
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :file-list="uploadList"
          :disabled="!props.canUpload"
          class="upload-dragger-v2"
        >
          <el-icon class="el-icon--upload"><i class="el-icon-upload" /></el-icon>
          <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
        </el-upload>
      </div>

      <el-form-item label="患者">
        <el-select
          v-model="form.patientId"
          class="w-full"
          filterable
          remote
          allow-create
          default-first-option
          reserve-keyword
          :remote-method="searchPatients"
          :loading="patientsLoading"
          placeholder="搜索患者编号或姓名，也可输入新编号"
          @change="handlePatientChange"
        >
          <el-option
            v-for="patient in patientOptions"
            :key="patient.patient_id"
            :label="`${patient.name} (${patient.patient_id})`"
            :value="patient.patient_id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="患者姓名（新患者可快速建档）">
        <el-input v-model="form.patientName" placeholder="例如 张三；留空则以患者编号建档" />
      </el-form-item>
      <el-form-item label="影像类型">
        <el-select v-model="form.imageType" class="w-full">
          <el-option label="全景片" value="panoramic" />
          <el-option label="根尖片" value="periapical" />
          <el-option label="CBCT" value="cbct" />
        </el-select>
      </el-form-item>

      <div v-if="fileMeta" class="upload-meta-v2">
        <div class="upload-meta-grid">
          <span>文件名：{{ fileMeta.name }}</span>
          <span>文件大小：{{ fileMeta.size }}</span>
          <span>文件类型：{{ fileMeta.type }}</span>
          <span>选择时间：{{ fileMeta.selectedAt }}</span>
        </div>
        <div v-if="previewUrl" class="upload-preview-v2">
          <img :src="previewUrl" alt="影像预览" />
        </div>
      </div>

      <div class="quick-action-row upload-actions-v2">
        <el-button type="primary" :loading="loading" :disabled="!props.canUpload" @click="handleSubmit">开始 AI 诊断</el-button>
        <el-tag v-if="uploadFile" type="info">{{ uploadFile.name }}</el-tag>
      </div>
    </el-form>

    <details class="event-box compact-details">
      <summary>实时分析事件（{{ socketEvents.length }}）</summary>
      <el-empty v-if="socketEvents.length === 0" description="上传后显示任务进度" />
      <el-timeline v-else>
        <el-timeline-item v-for="event in socketEvents" :key="event" :timestamp="'实时'">{{ event }}</el-timeline-item>
      </el-timeline>
    </details>
  </el-card>
</template>
