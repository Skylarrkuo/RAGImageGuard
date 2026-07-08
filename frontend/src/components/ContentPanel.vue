<template>
  <div class="content-panel">
    <div class="content-panel-header">
      <span>{{ title }}</span>
      <span>{{ time }}</span>
    </div>
    <div class="content-panel-body" ref="bodyRef">

      <!-- Loading state -->
      <div v-if="loading && !hasContent && !hasCompliance && !step4Images && activeStep !== 'step4'" class="content-loading">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div class="loading-text">正在生成</div>
      </div>

      <!-- Step 4: Generating animation (waiting for image) -->
      <div v-else-if="activeStep === 'step4' && loading && !step4Images" class="generating-container">
        <div class="generating-visual">
          <div class="generating-ring"></div>
          <div class="generating-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
        </div>
        <div class="generating-text">AI 正在生成图片</div>
        <div class="generating-subtext">根据提示词进行图像编辑，请稍候...</div>
        <div class="generating-progress">
          <div class="generating-progress-bar"></div>
        </div>
      </div>

      <!-- Step 4: Scan animation + thumbnail + lightbox -->
      <div v-else-if="activeStep === 'step4' && step4Images" class="compare-container">
        <!-- Scan reveal phase -->
        <div v-if="scanPhase" class="scan-reveal" :class="{ 'scan-done': scanDone }">
          <img :src="step4Images.generated" alt="Generated" class="scan-image" @load="onImageLoad" />
          <div class="scan-line"></div>
          <div class="scan-overlay">
            <div class="scan-label">Generating</div>
          </div>
        </div>

        <!-- Thumbnail phase (compact preview) -->
        <div v-else class="image-thumb-section">
          <div class="image-thumb-wrapper" @click="openLightbox('step4')">
            <img :src="step4Images.generated" alt="生成结果" class="image-thumb" />
            <div class="thumb-hover-overlay">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                <line x1="11" y1="8" x2="11" y2="14"/>
                <line x1="8" y1="11" x2="14" y2="11"/>
              </svg>
              <span>点击放大对比预览</span>
            </div>
          </div>
          <div class="thumb-actions">
            <button class="btn-thumb-expand" @click="openLightbox('step4')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="15 3 21 3 21 9"/>
                <polyline points="9 21 3 21 3 15"/>
                <line x1="21" y1="3" x2="14" y2="10"/>
                <line x1="3" y1="21" x2="10" y2="14"/>
              </svg>
              放大对比预览
            </button>
            <button class="btn-thumb-download" @click="downloadImage(step4Images.generated, 'step4')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              下载图片
            </button>
          </div>
        </div>

        <!-- Edit Summary Section -->
        <div v-if="step4Summary" class="edit-summary-section">
          <div class="summary-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
            <span>修改总结与建议</span>
          </div>
          <div class="summary-content md-content" v-html="renderMarkdown(step4Summary)"></div>
        </div>
      </div>

      <!-- Step 5: Scan animation + thumbnail + lightbox -->
      <div v-else-if="activeStep === 'step5' && step5Images" class="compare-container">
        <div v-if="scanPhase" class="scan-reveal" :class="{ 'scan-done': scanDone }">
          <img :src="step5Images.generated" alt="Refined" class="scan-image" @load="onImageLoad" />
          <div class="scan-line"></div>
          <div class="scan-overlay">
            <div class="scan-label">Refining</div>
          </div>
        </div>
        <div v-else class="image-thumb-section">
          <div class="image-thumb-wrapper" @click="openLightbox('step5')">
            <img :src="step5Images.generated" alt="精修结果" class="image-thumb" />
            <div class="thumb-hover-overlay">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                <line x1="11" y1="8" x2="11" y2="14"/>
                <line x1="8" y1="11" x2="14" y2="11"/>
              </svg>
              <span>点击放大对比预览</span>
            </div>
          </div>
          <div class="thumb-actions">
            <button class="btn-thumb-expand" @click="openLightbox('step5')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="15 3 21 3 21 9"/>
                <polyline points="9 21 3 21 3 15"/>
                <line x1="21" y1="3" x2="14" y2="10"/>
                <line x1="3" y1="21" x2="10" y2="14"/>
              </svg>
              放大对比预览
            </button>
            <button class="btn-thumb-download" @click="downloadImage(step5Images.generated, 'step5')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              下载图片
            </button>
          </div>
        </div>
      </div>

      <!-- Step 5: Generating animation (waiting for refined image) -->
      <div v-else-if="activeStep === 'step5' && loading && !step5Images" class="generating-container">
        <div class="generating-visual">
          <div class="generating-ring"></div>
          <div class="generating-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
        </div>
        <div class="generating-text">AI 正在精修图片</div>
        <div class="generating-subtext">根据修正提示词进行二次编辑，请稍候...</div>
        <div class="generating-progress">
          <div class="generating-progress-bar"></div>
        </div>
      </div>

      <!-- Step 5: Input area (before refinement runs) -->
      <div v-else-if="activeStep === 'step5' && !step5Images" class="refine-input-area">
        <div v-if="step4Images" class="refine-preview">
          <div class="image-thumb-wrapper" @click="openLightbox('step4')">
            <img :src="step4Images.generated" alt="当前图片" class="image-thumb" />
            <div class="thumb-hover-overlay">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                <line x1="11" y1="8" x2="11" y2="14"/>
                <line x1="8" y1="11" x2="14" y2="11"/>
              </svg>
              <span>点击放大对比预览</span>
            </div>
          </div>
          <div class="thumb-actions">
            <button class="btn-thumb-expand" @click="openLightbox('step4')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="15 3 21 3 21 9"/>
                <polyline points="9 21 3 21 3 15"/>
                <line x1="21" y1="3" x2="14" y2="10"/>
                <line x1="3" y1="21" x2="10" y2="14"/>
              </svg>
              放大对比预览
            </button>
            <button class="btn-thumb-download" @click="downloadImage(step4Images.generated, 'step4')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              下载图片
            </button>
          </div>
        </div>
        <div class="refine-form">
          <textarea
            v-model="refinePrompt"
            class="refine-textarea"
            placeholder="请输入修正提示词，描述你想要进一步修改的内容..."
            rows="4"
          ></textarea>
          <div class="refine-actions">
            <button
              class="btn btn-primary refine-btn"
              :disabled="!refinePrompt.trim()"
              @click="$emit('run-step5', refinePrompt.trim())"
            >
              开始修正
            </button>
            <button
              class="btn btn-outline refine-finish-btn"
              @click="$emit('finish-flow')"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              结束
            </button>
          </div>
        </div>
      </div>

      <!-- Compliance queries: structured collapsible sections -->
      <div v-else-if="activeStep === 'step2' && hasCompliance" class="compliance-sections">
        <div
          v-for="q in complianceQueries"
          :key="q.index"
          class="compliance-section"
          :class="{ collapsed: q.collapsed }"
        >
          <div class="compliance-header" @click="$emit('toggle-compliance', q.index)">
            <svg
              class="compliance-chevron"
              :class="{ rotated: !q.collapsed }"
              width="12" height="12" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" stroke-width="2.5"
              stroke-linecap="round" stroke-linejoin="round"
            >
              <polyline points="9 18 15 12 9 6"/>
            </svg>
            <span class="compliance-question">问题 {{ q.index + 1 }}：{{ q.question }}</span>
          </div>
          <div v-show="!q.collapsed" class="compliance-body">
            <div v-if="q.answer" class="md-content" v-html="renderMarkdown(q.answer)"></div>
            <div v-else class="compliance-pending">
              <span class="dot-pulse">等待回答</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Default content rendering -->
      <div v-else-if="loading && hasContent" class="content-streaming" v-html="content">
      </div>
      <div v-else v-html="content"></div>

      <!-- Streaming cursor -->
      <span v-if="loading && (hasContent || (activeStep === 'step2' && hasCompliance)) && !(activeStep === 'step4' && step4Images)" class="streaming-cursor"></span>
    </div>

    <!-- Lightbox overlay for full-size comparison -->
    <div v-if="lightboxOpen" class="lightbox-overlay" @click.self="closeLightbox">
      <div class="lightbox-content">
        <!-- Close button -->
        <button class="lightbox-close" @click="closeLightbox" title="关闭预览">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
        <!-- Download button -->
        <button class="lightbox-download" @click="downloadImage(lightboxImages?.generated, 'result')" title="下载图片">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
        </button>
        <!-- Compare slider in lightbox -->
        <div v-if="lightboxImages && lightboxImages.original" class="lightbox-compare" ref="lightboxCompareRef"
          @mousedown="startLightboxDrag"
          @touchstart.passive="startLightboxDrag"
        >
          <div class="compare-layer compare-layer-before" :style="{ clipPath: `inset(0 ${100 - lightboxSliderPos}% 0 0)` }">
            <img :src="lightboxImages.original" alt="Before" />
          </div>
          <div class="compare-layer compare-layer-after">
            <img :src="lightboxImages.generated" alt="After" />
          </div>
          <div class="compare-slider" :style="{ left: lightboxSliderPos + '%' }">
            <div class="compare-slider-line"></div>
            <div class="compare-slider-handle">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="15 18 9 12 15 6"/>
              </svg>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </div>
          </div>
          <div class="compare-label compare-label-before">Before</div>
          <div class="compare-label compare-label-after">After</div>
        </div>
        <div v-else-if="lightboxImages" class="lightbox-single">
          <img :src="lightboxImages.generated" alt="Result" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  title: { type: String, default: '等待开始' },
  time: { type: String, default: '' },
  content: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  activeStep: { type: String, default: '' },
  complianceQueries: { type: Array, default: () => [] },
  step4Images: { type: Object, default: null },
  step4Summary: { type: String, default: '' },
  step5Images: { type: Object, default: null },
})

defineEmits(['toggle-compliance', 'run-step5', 'finish-flow'])

// Step 5 refine prompt input
const refinePrompt = ref('')

const bodyRef = ref(null)
const compareRef = ref(null)

// Scan animation state
const scanPhase = ref(true)
const scanDone = ref(false)

// Compare slider state (kept for potential future use)
const sliderPos = ref(50)
const isDragging = ref(false)

// Lightbox state
const lightboxOpen = ref(false)
const lightboxImages = ref(null)
const lightboxSliderPos = ref(50)
const lightboxDragging = ref(false)
const lightboxCompareRef = ref(null)

const hasContent = computed(() => {
  return props.content && !props.content.includes('content-empty')
})

const hasCompliance = computed(() => {
  return props.complianceQueries && props.complianceQueries.length > 0
})

function renderMarkdown(text) {
  return marked.parse(text || '')
}

// When step4Images or step5Images arrives, start scan animation
watch(() => [props.step4Images, props.step5Images], ([v4, v5]) => {
  if (v4 || v5) {
    scanPhase.value = true
    scanDone.value = false
  }
}, { immediate: true })

// Image loaded → play scan animation then transition to compare
function onImageLoad() {
  requestAnimationFrame(() => {
    scanDone.value = true
  })
  setTimeout(() => {
    scanPhase.value = false
  }, 1800)
}

// ── Compare slider drag ──
function startDrag(e) {
  isDragging.value = true
  updateSlider(e)
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('touchmove', onDrag, { passive: false })
  window.addEventListener('mouseup', stopDrag)
  window.addEventListener('touchend', stopDrag)
}

function onDrag(e) {
  if (!isDragging.value) return
  e.preventDefault()
  updateSlider(e)
}

function stopDrag() {
  isDragging.value = false
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('touchmove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('touchend', stopDrag)
}

function updateSlider(e) {
  if (!compareRef.value) return
  const rect = compareRef.value.getBoundingClientRect()
  const touch = e.touches ? e.touches[0] : e
  const x = touch.clientX - rect.left
  sliderPos.value = Math.max(0, Math.min(100, (x / rect.width) * 100))
}

// ── Lightbox ──
function openLightbox(step) {
  if (step === 'step4') {
    lightboxImages.value = props.step4Images
  } else if (step === 'step5') {
    lightboxImages.value = props.step5Images
  }
  lightboxSliderPos.value = 50
  lightboxOpen.value = true
}

function closeLightbox() {
  lightboxOpen.value = false
  lightboxImages.value = null
}

// Close lightbox on Escape key
function onLightboxKeydown(e) {
  if (e.key === 'Escape') closeLightbox()
}

watch(lightboxOpen, (open) => {
  if (open) {
    window.addEventListener('keydown', onLightboxKeydown)
  } else {
    window.removeEventListener('keydown', onLightboxKeydown)
  }
})

function startLightboxDrag(e) {
  lightboxDragging.value = true
  updateLightboxSlider(e)
  window.addEventListener('mousemove', onLightboxDrag)
  window.addEventListener('touchmove', onLightboxDrag, { passive: false })
  window.addEventListener('mouseup', stopLightboxDrag)
  window.addEventListener('touchend', stopLightboxDrag)
}

function onLightboxDrag(e) {
  if (!lightboxDragging.value) return
  e.preventDefault()
  updateLightboxSlider(e)
}

function stopLightboxDrag() {
  lightboxDragging.value = false
  window.removeEventListener('mousemove', onLightboxDrag)
  window.removeEventListener('touchmove', onLightboxDrag)
  window.removeEventListener('mouseup', stopLightboxDrag)
  window.removeEventListener('touchend', stopLightboxDrag)
}

function updateLightboxSlider(e) {
  if (!lightboxCompareRef.value) return
  const rect = lightboxCompareRef.value.getBoundingClientRect()
  const touch = e.touches ? e.touches[0] : e
  const x = touch.clientX - rect.left
  lightboxSliderPos.value = Math.max(0, Math.min(100, (x / rect.width) * 100))
}

// ── Download image ──
function downloadImage(url, step) {
  const link = document.createElement('a')
  link.href = url
  link.download = `${step}_${Date.now()}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Auto-scroll to bottom when content changes
watch(() => [props.content, props.complianceQueries, props.step4Summary], async () => {
  await nextTick()
  if (bodyRef.value) {
    bodyRef.value.scrollTop = bodyRef.value.scrollHeight
  }
}, { deep: true })
</script>
