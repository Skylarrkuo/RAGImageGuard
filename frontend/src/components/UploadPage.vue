<template>
  <div class="page active">
    <div class="upload-page">
      <div class="upload-hero">
        <div class="upload-hero-overline">AI Visual Diagnosis</div>
        <h1 class="upload-hero-title">景区合规<br>智能诊断</h1>
        <p class="upload-hero-desc">上传景区实景照片，AI 自动识别场景、分析合规性、生成改进方案。</p>
      </div>

      <div class="upload-grid">
        <div
          class="upload-zone"
          :class="{ dragover }"
          @click="fileInput.click()"
          @dragover.prevent="dragover = true"
          @dragleave="dragover = false"
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            @change="handleInputChange"
          >
          <div class="upload-icon">
            <svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <div class="upload-title">点击或拖拽图片至此处</div>
          <div class="upload-hint">JPG · PNG · WebP — Max 20MB</div>
        </div>
        <div class="preview-area">
          <div class="preview-image-wrap">
            <img :class="{ show: previewUrl }" :src="previewUrl || ''" alt="Preview">
            <div v-if="!previewUrl" class="preview-placeholder">选择图片后预览</div>
          </div>
          <div v-if="selectedFile" class="preview-meta">
            <span class="preview-filename">{{ selectedFile.name }}</span>
            <span class="preview-size">{{ fileSize }}</span>
          </div>
        </div>
      </div>

      <div class="upload-actions">
        <button class="btn btn-primary" :disabled="!selectedFile" @click="startAnalysis">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          启动诊断
        </button>
        <button
          v-for="m in modes"
          :key="m.value"
          class="btn btn-ghost"
          :class="{ active: currentMode === m.value }"
          @click="currentMode = m.value"
        >
          {{ m.label }}
        </button>
        <button class="btn btn-ghost" @click="emit('show-history')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          历史记录
        </button>
      </div>

      <div class="config-strip">
        <div>
          <div class="config-item-label">MiMo Vision</div>
          <div class="config-item-value" :class="configClass('mimo')">{{ configText('mimo') }}</div>
        </div>
        <div>
          <div class="config-item-label">MaxKB RAG</div>
          <div class="config-item-value" :class="configClass('maxkb')">{{ configText('maxkb') }}</div>
        </div>
        <div>
          <div class="config-item-label">GPT Image</div>
          <div class="config-item-value" :class="configClass('openai')">{{ configText('openai') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { checkConfig } from '../api/index.js'

const emit = defineEmits(['start', 'show-history'])

const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref('')
const dragover = ref(false)
const currentMode = ref('full')
const config = ref(null)

const modes = [
  { value: 'full', label: '完整流程' },
  { value: 'step1', label: '仅识别' },
  { value: 'step2', label: '仅合规分析' },
]

const fileSize = computed(() => {
  if (!selectedFile.value) return ''
  return (selectedFile.value.size / 1024 / 1024).toFixed(1) + ' MB'
})

function configClass(key) {
  if (!config.value) return ''
  if (key === 'mimo') return config.value.mimo?.api_key_configured ? 'ok' : 'missing'
  if (key === 'maxkb') return config.value.maxkb?.scene_optimize_key_configured ? 'ok' : 'missing'
  if (key === 'openai') return config.value.openai?.api_key_configured ? 'ok' : 'missing'
  return ''
}

function configText(key) {
  if (!config.value) return '—'
  if (key === 'mimo') return config.value.mimo?.api_key_configured ? 'OK' : 'Missing'
  if (key === 'maxkb') return config.value.maxkb?.scene_optimize_key_configured ? 'OK' : 'Missing'
  if (key === 'openai') return config.value.openai?.api_key_configured ? 'OK' : 'Missing'
  return '—'
}

function handleFile(file) {
  if (!file.type.match(/^image\/(jpeg|jpg|png|webp)$/)) {
    alert('请上传 JPG/PNG/WebP')
    return
  }
  if (file.size > 20 * 1024 * 1024) {
    alert('不超过 20MB')
    return
  }
  selectedFile.value = file
  const reader = new FileReader()
  reader.onload = e => {
    previewUrl.value = e.target.result
  }
  reader.readAsDataURL(file)
}

function handleInputChange() {
  if (fileInput.value?.files.length) {
    handleFile(fileInput.value.files[0])
  }
}

function handleDrop(e) {
  dragover.value = false
  if (e.dataTransfer.files.length) {
    handleFile(e.dataTransfer.files[0])
  }
}

function startAnalysis() {
  if (!selectedFile.value) return
  emit('start', { file: selectedFile.value, mode: currentMode.value })
}

onMounted(async () => {
  try {
    config.value = await checkConfig()
  } catch {
    config.value = null
  }
})
</script>
