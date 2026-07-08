<template>
  <div class="page page-history active">
    <div class="history-container">

      <!-- List View -->
      <template v-if="!selectedRecord">
        <div class="history-header">
          <div>
            <div class="history-title">历史记录</div>
            <div class="history-count">{{ totalRecords }} 条分析记录</div>
          </div>
          <button class="btn btn-outline" @click="$emit('back')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
            返回
          </button>
        </div>

        <!-- Search Bar -->
        <div class="history-search">
          <input
            v-model="searchQuery"
            class="history-search-input"
            placeholder="搜索场景描述、提示词..."
            @input="onSearchInput"
          >
          <span v-if="searchQuery" class="history-search-clear" @click="searchQuery = ''; onSearchInput()">✕</span>
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

        <div v-else-if="records.length === 0 && searchQuery" class="history-empty">
          <div class="history-empty-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </div>
          <div class="history-empty-text">未找到匹配记录</div>
          <div class="history-empty-hint">尝试其他关键词</div>
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

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="history-pagination">
          <button class="btn btn-ghost history-page-btn" :disabled="currentPage <= 1" @click="goToPage(currentPage - 1)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
            上一页
          </button>
          <span class="history-page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button class="btn btn-ghost history-page-btn" :disabled="currentPage >= totalPages" @click="goToPage(currentPage + 1)">
            下一页
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
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
            <!-- Refined image comparison (generated vs refined) -->
            <div v-if="selectedRecord.refined_image && selectedRecord.generated_image" class="image-compare" ref="compareRef"
              @mousedown="startDrag" @touchstart.passive="startDrag"
            >
              <div class="compare-layer compare-layer-before" :style="{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }">
                <img :src="'/images/' + selectedRecord.generated_image" alt="Before (Step 4)" />
              </div>
              <div class="compare-layer compare-layer-after">
                <img :src="'/images/' + selectedRecord.refined_image" alt="After (Step 5)" />
              </div>
              <div class="compare-slider" :style="{ left: sliderPos + '%' }">
                <div class="compare-slider-line"></div>
                <div class="compare-slider-handle">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                </div>
              </div>
              <div class="compare-label compare-label-before">Step 4</div>
              <div class="compare-label compare-label-after">Step 5</div>
            </div>
            <!-- Original vs generated comparison -->
            <div v-else-if="selectedRecord.original_image && selectedRecord.generated_image" class="image-compare" ref="compareRef"
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
            <!-- Download buttons -->
            <div class="detail-download-actions">
              <button v-if="selectedRecord.original_image" class="btn btn-outline detail-download-btn" @click="downloadImage('/images/' + selectedRecord.original_image, 'original')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                下载原图
              </button>
              <button v-if="selectedRecord.generated_image" class="btn btn-outline detail-download-btn" @click="downloadImage('/images/' + selectedRecord.generated_image, 'generated')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                下载生成图
              </button>
              <button v-if="selectedRecord.refined_image" class="btn btn-outline detail-download-btn" @click="downloadImage('/images/' + selectedRecord.refined_image, 'refined')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                下载精修图
              </button>
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

            <!-- Step 4: Edit summary -->
            <div v-if="selectedRecord.edit_summary" class="detail-section">
              <div class="detail-section-title">修改总结</div>
              <div class="md-content" v-html="renderMarkdown(selectedRecord.edit_summary)"></div>
            </div>

            <!-- Step 5: Refine info -->
            <div v-if="selectedRecord.refine_prompt" class="detail-section">
              <div class="detail-section-title">补充编辑提示词</div>
              <div class="prompt-box">{{ selectedRecord.refine_prompt }}</div>
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
                <div v-if="selectedRecord.step5_ms" class="detail-time-item">
                  <span>补充编辑</span>
                  <span>{{ (selectedRecord.step5_ms / 1000).toFixed(1) }}s</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Delete Confirmation Modal -->
    <AppModal
      :visible="showDeleteModal"
      mode="confirm"
      title="删除确认"
      message="确定删除这条记录？删除后无法恢复。"
      confirm-text="删除"
      cancel-text="取消"
      @confirm="onConfirmDelete"
      @cancel="onCancelDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { marked } from 'marked'
import { getHistory, getHistoryDetail, deleteHistory } from '../api/index.js'
import AppModal from './AppModal.vue'

defineEmits(['back'])

const records = ref([])
const loading = ref(true)
const selectedRecord = ref(null)

// Search + Pagination
const searchQuery = ref('')
const currentPage = ref(1)
const totalPages = ref(1)
const totalRecords = ref(0)
const perPage = 12
let searchTimer = null

// Delete modal
const showDeleteModal = ref(false)
const pendingDeleteId = ref(null)

// Compare slider state
const compareRef = ref(null)
const sliderPos = ref(50)
const isDragging = ref(false)

onMounted(async () => {
  await fetchHistory()
})

async function fetchHistory() {
  loading.value = true
  try {
    const data = await getHistory(searchQuery.value, currentPage.value, perPage)
    if (data.success) {
      records.value = data.records
      totalPages.value = data.pages
      totalRecords.value = data.total
    }
  } finally {
    loading.value = false
  }
}

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    fetchHistory()
  }, 300)
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchHistory()
}

function viewDetail(record) {
  // Add reactive _collapsed property for toggling
  if (record.compliance_queries) {
    record.compliance_queries.forEach(q => { q._collapsed = true })
  }
  selectedRecord.value = record
}

function removeRecord(id) {
  pendingDeleteId.value = id
  showDeleteModal.value = true
}

async function onConfirmDelete() {
  const id = pendingDeleteId.value
  showDeleteModal.value = false
  pendingDeleteId.value = null
  if (!id) return
  const data = await deleteHistory(id)
  if (data.success) {
    records.value = records.value.filter(r => r.id !== id)
    totalRecords.value--
  }
}

function onCancelDelete() {
  showDeleteModal.value = false
  pendingDeleteId.value = null
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
  if (status === 'refined') return '已精修'
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

// ── Download image ──
function downloadImage(url, type) {
  const link = document.createElement('a')
  link.href = url
  link.download = `${type}_${Date.now()}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.page-history.active {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 52px);
  overflow: hidden;
}

.history-container {
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid var(--fg);
  margin-bottom: 1.5rem;
}

.history-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.5rem;
  font-weight: 700;
}

.history-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--neutral-500);
  margin-top: 0.25rem;
}

.history-search {
  position: relative;
  margin-bottom: 1.5rem;
}

.history-search-input {
  width: 100%;
  padding: 0.65rem 2.5rem 0.65rem 0.85rem;
  border: 2px solid var(--fg);
  background: var(--bg);
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  line-height: 1.6;
  transition: border-color 200ms;
}

.history-search-input:focus {
  outline: none;
  border-color: var(--accent);
}

.history-search-input::placeholder {
  color: var(--neutral-400);
}

.history-search-clear {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: var(--neutral-400);
  font-size: 0.85rem;
  transition: color 200ms;
}

.history-search-clear:hover {
  color: var(--accent);
}

.history-loading {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

.history-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 0;
  gap: 0.75rem;
}

.history-empty-icon { color: var(--neutral-400); }
.history-empty-text {
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--neutral-600);
}
.history-empty-hint {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: var(--neutral-400);
}

.history-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}
@media (min-width: 640px) {
  .history-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (min-width: 1024px) {
  .history-grid { grid-template-columns: repeat(3, 1fr); }
}

.history-card {
  border: 1px solid var(--fg);
  cursor: pointer;
  transition: box-shadow 200ms, transform 200ms;
  background: var(--bg);
}
.history-card:hover {
  box-shadow: 3px 3px 0px 0px var(--fg);
  transform: translate(-1.5px, -1.5px);
}

.history-card-image {
  height: 160px;
  background: var(--neutral-200);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.history-card-image :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.history-card-no-img {
  color: var(--neutral-400);
}

.history-card-body {
  padding: 0.75rem 1rem;
}

.history-card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
}

.history-card-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.55rem;
  letter-spacing: 0.1em;
  color: var(--neutral-500);
}

.history-card-status {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.1rem 0.5rem;
  border: 1px solid var(--muted);
  color: var(--neutral-500);
}
.history-card-status.completed {
  border-color: var(--success);
  color: var(--success);
}
.history-card-status.partial {
  border-color: var(--accent);
  color: var(--accent);
}
.history-card-status.refined {
  border-color: var(--success);
  color: var(--success);
}

.history-card-desc {
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  color: var(--neutral-600);
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.history-card-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  color: var(--neutral-400);
  transition: color 200ms;
}
.btn-icon:hover { color: var(--accent); }

.history-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--muted);
}

.history-page-btn {
  min-height: 36px;
  padding: 0 1rem;
  font-size: 0.55rem;
}

.history-page-info {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  color: var(--neutral-500);
}

.detail-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}
@media (min-width: 1024px) {
  .detail-layout { grid-template-columns: 1fr 1fr; }
}

.detail-images {
  position: sticky;
  top: 0;
  align-self: start;
}

.detail-single-image {
  border: 2px solid var(--fg);
}
.detail-single-image :deep(img) {
  width: 100%;
  display: block;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detail-section {
  border-bottom: 1px solid var(--muted);
  padding-bottom: 1.5rem;
}
.detail-section:last-child { border-bottom: none; }

.detail-section-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.75rem;
}

.detail-times {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.detail-time-item {
  display: flex;
  justify-content: space-between;
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  padding: 0.3rem 0;
  border-bottom: 1px dashed var(--muted);
}
.detail-time-item:last-child { border-bottom: none; }
.detail-time-item :deep(span:last-child) {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}

.detail-download-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.detail-download-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  font-size: 0.7rem;
}

.detail-download-btn :deep(svg) {
  flex-shrink: 0;
}
</style>
