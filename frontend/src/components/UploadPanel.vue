<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadUserFile } from 'element-plus'
import type { AnalysisItem } from '../types/analysis'

const emit = defineEmits<{
  submit: [payload: { file: File; patientId: string; imageType: AnalysisItem['image_type'] }]
}>()

const props = defineProps<{
  canUpload: boolean
}>()

const loading = defineModel<boolean>('loading', { required: true })
const socketEvents = defineModel<string[]>('socketEvents', { required: true })

const form = reactive({
  patientId: 'P-0001',
  imageType: 'panoramic' as AnalysisItem['image_type']
})
const uploadFile = ref<File | null>(null)
const uploadList = ref<UploadUserFile[]>([])

function handleFileChange(file: UploadUserFile) {
  uploadFile.value = file.raw ?? null
  uploadList.value = file ? [file] : []
}

function handleSubmit() {
  if (!uploadFile.value) {
    ElMessage.warning('请先选择影像文件')
    return
  }

  emit('submit', {
    file: uploadFile.value,
    patientId: form.patientId,
    imageType: form.imageType
  })
}
</script>

<template>
  <el-card class="panel" shadow="never">
    <template #header>
      <div class="panel-header">
        <span>影像上传</span>
        <el-tag>{{ form.imageType }}</el-tag>
      </div>
    </template>

    <el-form label-position="top">
      <div class="upload-dropzone">
        <div class="panel-header">
          <span>病例影像接入</span>
          <el-tag type="success">支持 DICOM / PNG / JPG</el-tag>
        </div>
        <p class="upload-hint">建议上传脱敏后的口腔影像文件，系统会自动进入 AI 分析与报告生成流程。</p>
      </div>
      <el-form-item label="患者 ID">
        <el-input v-model="form.patientId" placeholder="例如 P-0001" />
      </el-form-item>
      <el-form-item label="影像类型">
        <el-select v-model="form.imageType" class="w-full">
          <el-option label="全景片" value="panoramic" />
          <el-option label="根尖片" value="periapical" />
          <el-option label="CBCT" value="cbct" />
        </el-select>
      </el-form-item>
      <el-form-item label="影像文件">
        <el-upload :auto-upload="false" :limit="1" :on-change="handleFileChange" :file-list="uploadList" :disabled="!props.canUpload">
          <el-button type="primary" plain :disabled="!props.canUpload">选择文件</el-button>
        </el-upload>
      </el-form-item>
      <div class="quick-action-row">
        <el-button type="primary" :loading="loading" :disabled="!props.canUpload" @click="handleSubmit">上传并分析</el-button>
        <el-tag v-if="uploadFile" type="info">{{ uploadFile.name }}</el-tag>
      </div>
    </el-form>

    <div class="event-box">
      <div class="panel-header">
        <span>实时分析事件</span>
        <el-tag type="info">{{ socketEvents.length }} 条</el-tag>
      </div>
      <el-empty v-if="socketEvents.length === 0" description="上传后这里会显示 WebSocket 事件" />
      <el-timeline v-else>
        <el-timeline-item v-for="event in socketEvents" :key="event" :timestamp="'实时'">
          {{ event }}
        </el-timeline-item>
      </el-timeline>
    </div>
  </el-card>
</template>
