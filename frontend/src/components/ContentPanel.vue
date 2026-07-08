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

<style scoped>
.content-panel {
  border: 1px solid var(--fg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-panel-header {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--fg);
  background: var(--fg);
  color: var(--bg);
  display: flex;
  justify-content: space-between;
}

.content-panel-body {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.content-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--neutral-400);
}

.content-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 1.5rem;
}

.loading-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--neutral-500);
  animation: textFade 2s ease-in-out infinite;
}

@keyframes textFade {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--accent);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursorBlink 0.8s step-end infinite;
}

@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.query-divider {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--accent);
  padding: 1rem 0 0.5rem;
  border-top: 1px dashed var(--muted);
  margin-top: 1rem;
}
.query-divider:first-child { border-top: none; margin-top: 0; padding-top: 0; }

.compliance-sections {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.compliance-section {
  border-bottom: 1px solid var(--muted);
}
.compliance-section:last-child { border-bottom: none; }

.compliance-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 0;
  cursor: pointer;
  user-select: none;
  transition: color 200ms;
}
.compliance-header:hover { color: var(--accent); }

.compliance-chevron {
  flex-shrink: 0;
  transition: transform 200ms ease;
  color: var(--neutral-400);
}
.compliance-chevron.rotated { transform: rotate(90deg); }

.compliance-question {
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.4;
}

.compliance-body {
  padding: 0 0 1rem 1.25rem;
  border-left: 2px solid var(--muted);
  margin-left: 5px;
  overflow: hidden;
}

.compliance-pending {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: var(--neutral-400);
  padding: 0.5rem 0;
}

.dot-pulse::after {
  content: '';
  animation: dotPulseText 1.5s steps(4, end) infinite;
}
@keyframes dotPulseText {
  0% { content: ''; }
  25% { content: '.'; }
  50% { content: '..'; }
  75% { content: '...'; }
}

.compare-container {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 1.5rem;
}

.scan-reveal {
  position: relative;
  overflow: hidden;
  border: 2px solid var(--fg);
  background: var(--fg);
  width: 100%;
}

.scan-image {
  width: 100%;
  display: block;
  clip-path: inset(0 0 100% 0);
  transition: clip-path 1.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.scan-reveal.scan-done .scan-image {
  clip-path: inset(0 0 0% 0);
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent);
  box-shadow: 0 0 20px 4px var(--accent), 0 0 60px 8px rgba(204, 0, 0, 0.3);
  transform: translateY(-100%);
  z-index: 2;
}

.scan-reveal.scan-done .scan-line {
  animation: scanMove 1.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}

@keyframes scanMove {
  0% { transform: translateY(0); opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(calc(100vh)); opacity: 0; }
}

.scan-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(17, 17, 17, 0.6);
  z-index: 3;
  transition: opacity 0.4s ease 1.2s;
  pointer-events: none;
}

.scan-reveal.scan-done .scan-overlay {
  opacity: 0;
}

.scan-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--accent);
  animation: textFade 1s ease-in-out infinite;
}

.prompt-box {
  font-family: 'Lora', serif;
  font-size: 0.9rem;
  line-height: 1.8;
  padding: 1rem;
  border: 1px solid var(--fg);
  background: var(--neutral-100);
}

.generated-wrap {
  border: 2px solid var(--fg);
  width: 100%;
  transition: all 200ms ease-out;
}
.generated-wrap:hover {
  box-shadow: 4px 4px 0px 0px var(--fg);
  transform: translate(-2px, -2px);
}
.generated-wrap :deep(img) { width: 100%; display: block; }

.image-thumb-section {
  width: 100%;
  max-width: 900px;
}

.image-thumb-wrapper {
  position: relative;
  width: 240px;
  border: 2px solid var(--fg);
  cursor: pointer;
  overflow: hidden;
  transition: all 200ms ease-out;
}

.image-thumb-wrapper:hover {
  box-shadow: 4px 4px 0px 0px var(--fg);
  transform: translate(-2px, -2px);
}

.image-thumb-wrapper:hover .thumb-hover-overlay {
  opacity: 1;
}

.image-thumb {
  width: 100%;
  display: block;
}

.thumb-hover-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  background: rgba(17, 17, 17, 0.7);
  color: #fff;
  opacity: 0;
  transition: opacity 200ms ease;
  pointer-events: none;
}

.thumb-hover-overlay :deep(svg) {
  stroke: #fff;
}

.thumb-hover-overlay :deep(span) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.thumb-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  flex-wrap: wrap;
}

.btn-thumb-expand,
.btn-thumb-download {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.9rem;
  border: 1px solid var(--fg);
  background: var(--bg, #fff);
  color: var(--fg, #111);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-thumb-expand:hover,
.btn-thumb-download:hover {
  background: var(--fg, #111);
  color: var(--bg, #fff);
  box-shadow: 2px 2px 0px 0px var(--fg);
  transform: translate(-1px, -1px);
}

.btn-thumb-expand :deep(svg),
.btn-thumb-download :deep(svg) {
  flex-shrink: 0;
}

.lightbox-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  box-sizing: border-box;
  animation: lightboxFadeIn 200ms ease;
}

@keyframes lightboxFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.lightbox-content {
  position: relative;
  max-width: 95vw;
  max-height: 90vh;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-close {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  z-index: 10001;
  width: 44px;
  height: 44px;
  border: 2px solid #fff;
  background: rgba(17, 17, 17, 0.8);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 150ms ease;
}

.lightbox-close:hover {
  background: var(--accent, #cc0000);
  border-color: var(--accent, #cc0000);
  transform: scale(1.1);
}

.lightbox-download {
  position: fixed;
  top: 1.5rem;
  right: 5rem;
  z-index: 10001;
  width: 44px;
  height: 44px;
  border: 2px solid #fff;
  background: rgba(17, 17, 17, 0.8);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 150ms ease;
}

.lightbox-download:hover {
  background: var(--success, #2d7d46);
  border-color: var(--success, #2d7d46);
  transform: scale(1.1);
}

.lightbox-compare {
  position: relative;
  max-width: 95vw;
  max-height: 85vh;
  border: 2px solid #fff;
  cursor: ew-resize;
  user-select: none;
  overflow: hidden;
  line-height: 0;
}

.lightbox-compare :deep(.compare-layer img) {
  max-height: 85vh;
  width: auto;
  max-width: 95vw;
  display: block;
  pointer-events: none;
  object-fit: contain;
}

.lightbox-compare :deep(.compare-layer-before) {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1;
}

.lightbox-compare :deep(.compare-layer-after) {
  position: relative;
  z-index: 0;
}

.lightbox-compare :deep(.compare-slider) {
  position: absolute;
  top: 0;
  bottom: 0;
  z-index: 2;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.lightbox-compare :deep(.compare-slider-line) {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #fff;
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.6);
}

.lightbox-compare :deep(.compare-slider-handle) {
  position: relative;
  width: 44px;
  height: 44px;
  background: #fff;
  border: 2px solid var(--fg, #111);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
  pointer-events: auto;
  z-index: 3;
}

.lightbox-compare :deep(.compare-slider-handle svg) {
  stroke: var(--fg, #111);
  flex-shrink: 0;
}

.lightbox-compare :deep(.compare-label) {
  position: absolute;
  bottom: 1rem;
  z-index: 4;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  padding: 0.3rem 0.8rem;
  background: rgba(17, 17, 17, 0.8);
  color: #fff;
  pointer-events: none;
}

.lightbox-compare :deep(.compare-label-before) {
  left: 1rem;
}

.lightbox-compare :deep(.compare-label-after) {
  right: 1rem;
}

.lightbox-single {
  max-width: 95vw;
  max-height: 85vh;
}

.lightbox-single :deep(img) {
  max-width: 95vw;
  max-height: 85vh;
  display: block;
  object-fit: contain;
}

.edit-summary-section {
  border: 1px solid var(--fg);
  background: var(--neutral-100);
  width: 100%;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--fg);
  background: var(--fg);
  color: var(--bg);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.summary-header :deep(svg) {
  stroke: var(--bg);
  fill: none;
}

.summary-content {
  padding: 1rem;
  font-size: 0.85rem;
  line-height: 1.7;
}

.summary-content :deep(h3) {
  font-size: 0.9rem;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  padding-left: 0.75rem;
  border-left: 3px solid var(--accent);
}

.summary-content :deep(h3:first-child) {
  margin-top: 0;
}

.summary-content :deep(ul) {
  padding-left: 1.5rem;
  margin: 0.5rem 0;
}

.summary-content :deep(li) {
  margin: 0.3rem 0;
}

.generating-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
  gap: 1.5rem;
}

.generating-visual {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.generating-ring {
  position: absolute;
  inset: 0;
  border: 3px solid var(--muted);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: ringRotate 1.5s linear infinite;
}

@keyframes ringRotate {
  to { transform: rotate(360deg); }
}

.generating-icon {
  color: var(--neutral-500);
  animation: iconPulse 2s ease-in-out infinite;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.1); opacity: 1; }
}

.generating-text {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  color: var(--fg);
}

.generating-subtext {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  color: var(--neutral-500);
  text-align: center;
}

.generating-progress {
  width: 200px;
  height: 3px;
  background: var(--muted);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.generating-progress-bar {
  height: 100%;
  background: var(--accent);
  width: 30%;
  border-radius: 2px;
  animation: progressSlide 2s ease-in-out infinite;
}

@keyframes progressSlide {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(200%); }
  100% { transform: translateX(-100%); }
}

.refine-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 1.5rem;
}

.refine-input-area {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
}

.refine-preview {
  width: 100%;
}

.refine-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.refine-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--bg-card);
  border: 2px solid var(--fg);
  color: var(--fg);
  font-family: 'Noto Sans SC', 'Inter', sans-serif;
  font-size: 0.85rem;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 200ms;
}

.refine-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.refine-textarea::placeholder {
  color: var(--neutral-400);
}

.refine-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.refine-btn {
  padding: 0.6rem 1.5rem;
  font-size: 0.85rem;
}

.refine-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.refine-finish-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.6rem 1.2rem;
  font-size: 0.85rem;
  color: var(--fg);
  border: 1px solid var(--fg);
  background: transparent;
  cursor: pointer;
  transition: all 150ms ease;
}

.refine-finish-btn:hover {
  background: var(--fg);
  color: var(--bg);
}
</style>
