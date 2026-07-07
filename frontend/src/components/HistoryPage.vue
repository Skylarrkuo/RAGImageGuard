<template>
  <div class="page page-history active">
    <div class="history-container">

      <!-- List View -->
      <template v-if="!selectedRecord">
        <div class="history-header">
          <div>
            <div class="history-title">历史记录</div>
            <div class="history-count">{{ records.length }} 条分析记录</div>
          </div>
          <button class="btn btn-outline" @click="$emit('back')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
            返回
          </button>
        </div>

        <div v-if="loading" class="history-loading">
          <div class="loading-dots"><span></span><span></span><span></span></div>
        </div>

        <div v-else-if="records.length === 0" class="history-empty">
          <div class="history-empty-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <div class="history-empty-text">暂无分析记录</div>
          <div class="history-empty-hint">上传图片开始第一次分析</div>
        </div>

        <div v-else class="history-grid">
          <div
            v-for="record in records"
            :key="record.id"
            class="history-card"
            @click="viewDetail(record)"
          >
            <div class="history-card-image">
              <img v-if="record.original_image" :src="thumbUrl(record.original_image)" alt="" @error="$event.target.src='/images/'+record.original_image" />
              <div v-else class="history-card-no-img">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              </div>
            </div>
            <div class="history-card-body">
              <div class="history-card-meta">
                <span class="history-card-time">{{ formatTime(record.created_at) }}</span>
                <span class="history-card-status" :class="record.status">{{ statusLabel(record.status) }}</span>
              </div>
              <div class="history-card-desc">{{ truncate(record.scene_description, 80) }}</div>
              <div class="history-card-actions">
                <button class="btn-icon" title="删除" @click.stop="removeRecord(record.id)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Detail View -->
      <template v-else>
        <div class="history-header">
          <div>
            <div class="history-title">分析详情</div>
            <div class="history-count">{{ formatTime(selectedRecord.created_at) }}</div>
          </div>
          <button class="btn btn-outline" @click="selectedRecord = null">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
            返回列表
          </button>
        </div>

        <div class="detail-layout">
          <!-- Left: Image comparison -->
          <div class="detail-images">
            <div v-if="selectedRecord.original_image && selectedRecord.generated_image" class="image-compare" ref="compareRef"
              @mousedown="startDrag" @touchstart.passive="startDrag"
            >
              <div class="compare-layer compare-layer-before" :style="{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }">
                <img :src="'/images/' + selectedRecord.original_image" alt="Before" />
              </div>
              <div class="compare-layer compare-layer-after">
                <img :src="'/images/' + selectedRecord.generated_image" alt="After" />
              </div>
              <div class="compare-slider" :style="{ left: sliderPos + '%' }">
                <div class="compare-slider-line"></div>
                <div class="compare-slider-handle">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                </div>
              </div>
              <div class="compare-label compare-label-before">Before</div>
              <div class="compare-label compare-label-after">After</div>
            </div>
            <div v-else-if="selectedRecord.original_image" class="detail-single-image">
              <img :src="'/images/' + selectedRecord.original_image" alt="Original" />
            </div>
          </div>

          <!-- Right: Analysis results -->
          <div class="detail-content">
            <!-- Step 1: Scene description -->
            <div v-if="selectedRecord.scene_description" class="detail-section">
              <div class="detail-section-title">场景识别</div>
              <div class="md-content" v-html="renderMarkdown(selectedRecord.scene_description)"></div>
            </div>

            <!-- Step 2: Compliance analysis -->
            <div v-if="selectedRecord.compliance_queries && selectedRecord.compliance_queries.length > 0" class="detail-section">
              <div class="detail-section-title">合规分析</div>
              <div v-for="q in selectedRecord.compliance_queries" :key="q.index" class="compliance-section">
                <div class="compliance-header" @click="q._collapsed = !q._collapsed">
                  <svg class="compliance-chevron" :class="{ rotated: !q._collapsed }" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                  <span class="compliance-question">问题 {{ q.index + 1 }}：{{ q.question }}</span>
                </div>
                <div v-show="!q._collapsed" class="compliance-body">
                  <div class="md-content" v-html="renderMarkdown(q.answer)"></div>
                </div>
              </div>
            </div>
            <div v-else-if="selectedRecord.compliance_analysis" class="detail-section">
              <div class="detail-section-title">合规分析</div>
              <div class="md-content" v-html="renderMarkdown(selectedRecord.compliance_analysis)"></div>
            </div>

            <!-- Step 3: Edit prompt -->
            <div v-if="selectedRecord.edit_prompt" class="detail-section">
              <div class="detail-section-title">编辑提示词</div>
              <div class="prompt-box">{{ selectedRecord.edit_prompt }}</div>
            </div>

            <!-- Step times -->
            <div v-if="selectedRecord.step_times" class="detail-section">
              <div class="detail-section-title">耗时统计</div>
              <div class="detail-times">
                <div v-if="selectedRecord.step_times.step1_ms" class="detail-time-item">
                  <span>场景识别</span>
                  <span>{{ (selectedRecord.step_times.step1_ms / 1000).toFixed(1) }}s</span>
                </div>
                <div v-if="selectedRecord.step_times.step2_ms" class="detail-time-item">
                  <span>合规分析</span>
                  <span>{{ (selectedRecord.step_times.step2_ms / 1000).toFixed(1) }}s</span>
                </div>
                <div v-if="selectedRecord.step_times.step3_ms" class="detail-time-item">
                  <span>生成提示词</span>
                  <span>{{ (selectedRecord.step_times.step3_ms / 1000).toFixed(1) }}s</span>
                </div>
                <div v-if="selectedRecord.step_times.step4_ms" class="detail-time-item">
                  <span>图片编辑</span>
                  <span>{{ (selectedRecord.step_times.step4_ms / 1000).toFixed(1) }}s</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { marked } from 'marked'
import { getHistory, getHistoryDetail, deleteHistory } from '../api/index.js'

defineEmits(['back'])

const records = ref([])
const loading = ref(true)
const selectedRecord = ref(null)

// Compare slider state
const compareRef = ref(null)
const sliderPos = ref(50)
const isDragging = ref(false)

onMounted(async () => {
  try {
    const data = await getHistory()
    if (data.success) {
      records.value = data.records
    }
  } finally {
    loading.value = false
  }
})

function viewDetail(record) {
  // Add reactive _collapsed property for toggling
  if (record.compliance_queries) {
    record.compliance_queries.forEach(q => { q._collapsed = true })
  }
  selectedRecord.value = record
}

async function removeRecord(id) {
  if (!confirm('确定删除这条记录？')) return
  const data = await deleteHistory(id)
  if (data.success) {
    records.value = records.value.filter(r => r.id !== id)
  }
}

function formatTime(iso) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso
  }
}

function statusLabel(status) {
  if (status === 'completed') return '完成'
  if (status === 'partial') return '部分'
  return status || '—'
}

function truncate(text, len) {
  if (!text) return '无描述'
  return text.length > len ? text.slice(0, len) + '…' : text
}

function thumbUrl(filepath) {
  // original/abc123.jpg → /images/thumb/thumb_abc123.jpg
  const base = filepath.replace(/^.*\//, '').replace(/\.[^.]+$/, '')
  return '/images/thumb/thumb_' + base + '.jpg'
}

function renderMarkdown(text) {
  return marked.parse(text || '')
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
</script>
