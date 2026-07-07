<template>
  <div class="content-panel">
    <div class="content-panel-header">
      <span>{{ title }}</span>
      <span>{{ time }}</span>
    </div>
    <div class="content-panel-body" ref="bodyRef">
      <!-- Loading state -->
      <div v-if="loading && !hasContent && !hasCompliance && !step4Images" class="content-loading">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div class="loading-text">正在生成</div>
      </div>

      <!-- Step 4: Scan animation + compare slider -->
      <div v-else-if="activeStep === 'step4' && step4Images" class="compare-container">
        <!-- Scan reveal phase -->
        <div v-if="scanPhase" class="scan-reveal" :class="{ 'scan-done': scanDone }">
          <img :src="step4Images.generated" alt="Generated" class="scan-image" @load="onImageLoad" />
          <div class="scan-line"></div>
          <div class="scan-overlay">
            <div class="scan-label">Generating</div>
          </div>
        </div>

        <!-- Compare slider phase (only if both images exist) -->
        <div v-else-if="step4Images.original" class="image-compare" ref="compareRef"
          @mousedown="startDrag"
          @touchstart.passive="startDrag"
        >
          <!-- Before image (clipped) -->
          <div class="compare-layer compare-layer-before" :style="{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }">
            <img :src="step4Images.original" alt="Before" />
          </div>
          <!-- After image (full) -->
          <div class="compare-layer compare-layer-after">
            <img :src="step4Images.generated" alt="After" />
          </div>
          <!-- Slider -->
          <div class="compare-slider" :style="{ left: sliderPos + '%' }">
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
          <!-- Labels -->
          <div class="compare-label compare-label-before">Before</div>
          <div class="compare-label compare-label-after">After</div>
        </div>
        <!-- Fallback: no original image, just show generated -->
        <div v-else class="generated-wrap">
          <img :src="step4Images.generated" alt="Generated" />
        </div>
      </div>

      <!-- Step 5: Result compare slider (after refinement completes) -->
      <div v-else-if="activeStep === 'step5' && step5Images" class="compare-container">
        <div v-if="scanPhase" class="scan-reveal" :class="{ 'scan-done': scanDone }">
          <img :src="step5Images.generated" alt="Refined" class="scan-image" @load="onImageLoad" />
          <div class="scan-line"></div>
          <div class="scan-overlay">
            <div class="scan-label">Refining</div>
          </div>
        </div>
        <div v-else-if="step5Images.original" class="image-compare" ref="compareRef"
          @mousedown="startDrag"
          @touchstart.passive="startDrag"
        >
          <div class="compare-layer compare-layer-before" :style="{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }">
            <img :src="step5Images.original" alt="Before" />
          </div>
          <div class="compare-layer compare-layer-after">
            <img :src="step5Images.generated" alt="After" />
          </div>
          <div class="compare-slider" :style="{ left: sliderPos + '%' }">
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
        <div v-else class="generated-wrap">
          <img :src="step5Images.generated" alt="Refined" />
        </div>
      </div>

      <!-- Step 5: Input area (before refinement runs) -->
      <div v-else-if="activeStep === 'step5' && !step5Images" class="refine-input-area">
        <div v-if="step4Images" class="refine-preview">
          <img :src="step4Images.generated" alt="当前图片" />
        </div>
        <div class="refine-form">
          <textarea
            v-model="refinePrompt"
            class="refine-textarea"
            placeholder="请输入修正提示词，描述你想要进一步修改的内容..."
            rows="4"
          ></textarea>
          <button
            class="btn btn-primary refine-btn"
            :disabled="!refinePrompt.trim()"
            @click="$emit('run-step5', refinePrompt.trim())"
          >
            开始修正
          </button>
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
  step5Images: { type: Object, default: null },
})

defineEmits(['toggle-compliance', 'run-step5'])

// Step 5 refine prompt input
const refinePrompt = ref('')

const bodyRef = ref(null)
const compareRef = ref(null)

// Scan animation state
const scanPhase = ref(true)
const scanDone = ref(false)

// Compare slider state
const sliderPos = ref(50)
const isDragging = ref(false)

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

// Auto-scroll to bottom when content changes
watch(() => [props.content, props.complianceQueries], async () => {
  await nextTick()
  if (bodyRef.value) {
    bodyRef.value.scrollTop = bodyRef.value.scrollHeight
  }
}, { deep: true })
</script>
