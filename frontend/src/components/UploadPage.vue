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

<style scoped>
.upload-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 3rem 1.5rem;
}

.upload-hero {
  text-align: center;
  padding: 3rem 0 2rem;
  border-bottom: 1px solid var(--fg);
  margin-bottom: 2rem;
}
.upload-hero-overline {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 1rem;
}
.upload-hero-title {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2rem, 6vw, 4.5rem);
  font-weight: 900;
  line-height: 0.9;
  letter-spacing: -0.03em;
  margin-bottom: 1rem;
}
.upload-hero-desc {
  font-size: 1rem;
  color: var(--neutral-600);
  max-width: 500px;
  margin: 0 auto;
}

.upload-grid {
  display: grid;
  grid-template-columns: 1fr;
  border: 2px solid var(--fg);
}
@media (min-width: 768px) { .upload-grid { grid-template-columns: 1fr 1fr; } }
.upload-grid > :deep(*) + :deep(*) { border-top: 2px solid var(--fg); }
@media (min-width: 768px) {
  .upload-grid > :deep(*) + :deep(*) { border-top: none; border-left: 2px solid var(--fg); }
}

.upload-zone {
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 350px;
  cursor: pointer;
  transition: background 200ms;
}
.upload-zone:hover { background: var(--neutral-100); }
.upload-zone.dragover { background: var(--neutral-100); }
.upload-zone :deep(input) { display: none; }

.upload-icon {
  width: 60px; height: 60px;
  border: 2px solid var(--fg);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 1.5rem;
}
.upload-icon :deep(svg) { width: 24px; height: 24px; stroke: var(--fg); fill: none; stroke-width: 1.5; }

.upload-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.2rem;
  font-style: italic;
  margin-bottom: 0.5rem;
}
.upload-hint {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--neutral-500);
}

.preview-area {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}
.preview-image-wrap {
  flex: 1;
  background: var(--neutral-200);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  position: relative;
  overflow: hidden;
}
.preview-image-wrap :deep(img) {
  width: 100%; height: 100%;
  object-fit: cover;
  display: none;
}
.preview-image-wrap :deep(img.show) { display: block; }
.preview-placeholder {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--neutral-400);
}
.preview-meta {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0 0;
  border-top: 1px solid var(--fg);
  margin-top: 0.75rem;
}
.preview-filename {
  font-family: 'Playfair Display', serif;
  font-style: italic;
  font-size: 0.85rem;
}
.preview-size {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  color: var(--neutral-500);
}

.upload-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  flex-wrap: wrap;
}

.config-strip {
  display: flex;
  gap: 2rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--muted);
  flex-wrap: wrap;
}
.config-item-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.55rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--neutral-500);
}
.config-item-value {
  font-family: 'Inter', sans-serif;
  font-size: 0.7rem;
  font-weight: 600;
  margin-top: 0.15rem;
}
.config-item-value.ok { color: var(--success); }
.config-item-value.missing { color: var(--accent); }

@media (max-width: 767px) {
  .upload-hero-title { font-size: 2rem; }
}
</style>
