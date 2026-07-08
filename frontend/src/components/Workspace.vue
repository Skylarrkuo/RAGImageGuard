<template>
  <div class="page page-workspace active">
    <div class="workspace">

      <!-- Pipeline Header -->
      <div class="pipeline-header">
        <div class="pipeline-title">{{ title }}</div>
        <div class="pipeline-status">
          <div class="dot" :class="statusDotClass"></div>
          <span>{{ statusText }}</span>
        </div>
      </div>

      <div class="ws-layout">
        <!-- Sidebar: Pipeline Nodes -->
        <PipelineSidebar
          :nodes="nodes"
          :active-step="currentStep"
          @focus="focusStep"
          @retry="retryStep"
          @toggle-compliance="toggleCompliance"
        />

        <!-- Content Panel -->
        <ContentPanel
          :title="panelTitle"
          :time="panelTime"
          :content="panelContent"
          :loading="panelLoading"
          :active-step="currentStep"
          :compliance-queries="complianceQueries"
          :step4-images="step4Images"
          :step4-summary="editSummary"
          :step5-images="step5Images"
          @toggle-compliance="toggleCompliance"
          @run-step5="runStep5"
          @finish-flow="finishFlow"
        />
      </div>

      <!-- Summary Bar -->
      <SummaryBar
        v-if="showSummary"
        :step1="summary.step1"
        :step2="summary.step2"
        :step3="summary.step3"
        :total="summary.total"
      />

      <!-- Back Button -->
      <div style="margin-top: 1.5rem;">
        <button class="btn btn-outline" @click="$emit('back')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
          返回上传
        </button>
      </div>

      <!-- Step2 输入 Modal -->
      <AppModal
        :visible="showPromptModal"
        mode="prompt"
        title="场景描述"
        message="请输入场景描述以进行合规分析："
        placeholder="输入场景描述..."
        confirm-text="开始分析"
        cancel-text="返回"
        @confirm="onStep2Confirm"
        @cancel="onStep2Cancel"
      />

      <!-- 通用提示 Modal（替代 alert） -->
      <AppModal
        :visible="showInfoModal"
        mode="confirm"
        :title="infoModalTitle"
        :message="infoModalMessage"
        confirm-text="确定"
        @confirm="showInfoModal = false"
        @cancel="showInfoModal = false"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import { recognize, analyzeCompliance, generatePrompt, generateImage, refineImage, completeFlow, fullPipelineStream, consumeSSEStream } from '../api/index.js'
import PipelineSidebar from './PipelineSidebar.vue'
import ContentPanel from './ContentPanel.vue'
import SummaryBar from './SummaryBar.vue'
import AppModal from './AppModal.vue'

const props = defineProps({
  file: { type: File, required: true },
  mode: { type: String, default: 'full' },
})

const emit = defineEmits(['back', 'update:loading'])

// Step2 prompt modal
const showPromptModal = ref(false)

// 通用提示 Modal（替代 alert）
const showInfoModal = ref(false)
const infoModalTitle = ref('')
const infoModalMessage = ref('')

function showInfo(title, message) {
  infoModalTitle.value = title
  infoModalMessage.value = message
  showInfoModal.value = true
}

// Pipeline state
const title = ref('诊断进行中...')
const status = ref('running') // running | done | error
const currentStep = ref('step1')
const panelTime = ref('')
const showSummary = ref(false)

// Node states: { step1: { state, timeMs }, ... }
const nodes = ref({
  step1: { label: '场景识别', state: 'pending', timeMs: null, badge: 'Pending' },
  step2: { label: '合规分析', state: 'pending', timeMs: null, badge: 'Pending', children: [] },
  step3: { label: '生成提示词', state: 'pending', timeMs: null, badge: 'Pending' },
  step4: { label: '图片编辑', state: 'pending', timeMs: null, badge: 'Pending' },
  step5: { label: '补充编辑', state: 'pending', timeMs: null, badge: 'Pending' },
})

// Content for each step
const stepContents = ref({})

// Structured compliance queries (question + collapsible answer)
const complianceQueries = ref([])

// Step 4 image comparison data
const step4Images = ref(null) // { original, generated }

// Step 4 edit summary
const editSummary = ref('')

// Step 5 image comparison data
const step5Images = ref(null) // { original, generated }

// Intermediate results for retry support
const context = ref({
  sceneDescription: null,
  complianceAnalysis: null,
  editPrompt: null,
  originalUrl: null,
  generatedUrl: null,
  historyId: null,
})

// Summary times
const summary = ref({ step1: '—', step2: '—', step3: '—', total: '—' })

const statusDotClass = computed(() => {
  if (status.value === 'running') return 'running'
  if (status.value === 'done') return 'done'
  return ''
})

const statusText = computed(() => {
  if (status.value === 'running') return 'Running'
  if (status.value === 'done') return 'Complete'
  return 'Error'
})

const panelTitle = computed(() => {
  const titles = {
    step1: '场景识别结果',
    step2: '合规分析结果',
    step3: '编辑提示词',
    step4: '改进效果预览',
    step5: '补充编辑',
  }
  return titles[currentStep.value] || '等待开始'
})

const panelContent = computed(() => {
  const raw = stepContents.value[currentStep.value]
  if (!raw) return '<div class="content-empty">等待数据...</div>'
  // step2: 如果有结构化数据则由 ContentPanel 渲染，否则回退到 markdown
  if (currentStep.value === 'step2' && complianceQueries.value.length > 0) {
    return '' // ContentPanel 使用 complianceQueries prop 渲染
  }
  if (currentStep.value === 'step2') {
    return renderMarkdown(raw)
  }
  // step4: 如果有对比数据则由 ContentPanel 渲染
  if (currentStep.value === 'step4' && step4Images.value) {
    return '' // ContentPanel 使用 step4Images prop 渲染
  }
  // step5: 由 ContentPanel 渲染输入框或对比图
  if (currentStep.value === 'step5') {
    return '' // ContentPanel 使用 step5Images prop 渲染
  }
  return raw
})

const panelLoading = computed(() => {
  const node = nodes.value[currentStep.value]
  return node && node.state === 'running'
})

function focusStep(stepId) {
  currentStep.value = stepId
}

function setNodeState(stepId, state, timeMs) {
  const node = nodes.value[stepId]
  node.state = state
  if (timeMs !== undefined) {
    node.timeMs = timeMs
  }
  if (state === 'running') node.badge = 'Running'
  else if (state === 'success') node.badge = 'Done'
  else if (state === 'error') node.badge = 'Failed'
  else node.badge = 'Pending'
}

function renderMarkdown(text) {
  return `<div class="md-content">${marked.parse(text)}</div>`
}

function setStepContent(stepId, html) {
  stepContents.value[stepId] = html
}

function appendStepStream(stepId, text) {
  if (!stepContents.value[stepId]) {
    stepContents.value[stepId] = ''
  }
  stepContents.value[stepId] += text
}

function toggleCompliance(index) {
  const q = complianceQueries.value[index]
  if (q) q.collapsed = !q.collapsed
}

// Run analysis based on mode
async function runAnalysis() {
  emit('update:loading', true)

  try {
    if (props.mode === 'full') {
      await runFullPipeline()
    } else if (props.mode === 'step1') {
      await runStep1Only()
    } else if (props.mode === 'step2') {
      await runStep2Only()
    }
  } catch (e) {
    showInfo('分析失败', e.message)
  } finally {
    emit('update:loading', false)
    // Check if any node (except step5) has error state
    const hasError = Object.entries(nodes.value)
      .some(([id, n]) => id !== 'step5' && n.state === 'error')
    if (hasError) {
      status.value = 'error'
      title.value = '诊断出错 — 可点击重试失败步骤'
    } else {
      status.value = 'done'
      title.value = '诊断完成 — 可使用补充编辑进一步修正'
    }
  }
}

async function runFullPipeline() {
  const reader = await fullPipelineStream(props.file)

  await consumeSSEStream(reader, (ev) => {
    // Original image URL
    if (ev.type === 'original') {
      context.value.originalUrl = ev.url
    }

    // Step events
    if (ev.type === 'step') {
      const stepMap = { recognize: 'step1', compliance: 'step2', prompt: 'step3', image_edit: 'step4' }
      const stepId = stepMap[ev.step]

      if (ev.status === 'running') {
        setNodeState(stepId, 'running')
        focusStep(stepId)
        if (stepId === 'step4') step4Images.value = null
      } else {
        const timeMs = ev.time_ms || 0
        if (ev.success === false) {
          setNodeState(stepId, 'error', timeMs)
          setStepContent(stepId, `<div class="md-content" style="color:var(--accent)">✗ ${ev.error || '处理失败'}</div>`)
        } else {
          setNodeState(stepId, 'success', timeMs)
          if (stepId === 'step1') {
            context.value.sceneDescription = ev.description
            setStepContent(stepId, renderMarkdown(ev.description))
          } else if (stepId === 'step2') {
            context.value.complianceAnalysis = ev.analysis
            // 如果没有通过流式构建 complianceQueries，回退到纯文本
            if (complianceQueries.value.length === 0) {
              stepContents.value.step2 = ev.analysis
            }
          } else if (stepId === 'step3') {
            context.value.editPrompt = ev.prompt
            setStepContent(stepId, `<div class="prompt-box">${ev.prompt}</div>`)
          } else if (stepId === 'step4') {
            if (ev.success && ev.image_url) {
              step4Images.value = {
                original: context.value.originalUrl,
                generated: ev.image_url,
              }
              context.value.generatedUrl = ev.image_url
              // 保存修改总结
              if (ev.summary) {
                editSummary.value = ev.summary
              }
              // 激活 Step 5
              setNodeState('step5', 'pending')
              focusStep('step5')
            }
          }
        }
        // Update summary
        if (stepId === 'step1') summary.value.step1 = (timeMs / 1000).toFixed(1) + 's'
        if (stepId === 'step2') summary.value.step2 = (timeMs / 1000).toFixed(1) + 's'
        if (stepId === 'step3') summary.value.step3 = (timeMs / 1000).toFixed(1) + 's'
      }
    }

    // Compliance query (sub-question)
    if (ev.type === 'compliance_query') {
      nodes.value.step2.children.push({
        id: `child-${ev.index}`,
        index: ev.index,
        question: ev.question,
        state: 'running',
      })
      complianceQueries.value.push({
        index: ev.index,
        question: ev.question,
        answer: '',
        collapsed: false, // 新问题展开显示
      })
    }

    // Compliance chunk (streaming content → 精确匹配到对应问题)
    if (ev.type === 'compliance_chunk') {
      const targetQuery = complianceQueries.value.find(q => q.index === ev.index)
      if (targetQuery) {
        targetQuery.answer += ev.text
      }
    }

    // Query end → 折叠已完成的回答
    if (ev.type === 'query_end') {
      const child = nodes.value.step2.children.find(c => c.id === `child-${ev.index}`)
      if (child) child.state = 'success'
      const query = complianceQueries.value.find(q => q.index === ev.index)
      if (query) query.collapsed = true
    }

    // Done
    if (ev.type === 'done') {
      const totalMs = ev.total_time_ms
      summary.value.total = (totalMs / 1000).toFixed(1) + 's'
      showSummary.value = true
      panelTime.value = (totalMs / 1000).toFixed(1) + 's'
      if (ev.history_id) {
        context.value.historyId = ev.history_id
      }
    }
  })
}

async function runStep1Only() {
  setNodeState('step1', 'running')
  focusStep('step1')

  const data = await recognize(props.file)

  if (data.success) {
    context.value.sceneDescription = data.description
    setNodeState('step1', 'success', data.time_ms)
    setStepContent('step1', renderMarkdown(data.description))
    summary.value.step1 = (data.time_ms / 1000).toFixed(1) + 's'
    showSummary.value = true
  } else {
    setNodeState('step1', 'error')
    setStepContent('step1', `<div style="color:var(--accent)">✗ ${data.error}</div>`)
  }
}

async function runStep2Only() {
  showPromptModal.value = true
}

async function onStep2Confirm(desc) {
  showPromptModal.value = false
  if (!desc) {
    emit('back')
    return
  }

  setNodeState('step2', 'running')
  focusStep('step2')

  const data = await analyzeCompliance(desc)

  if (data.success) {
    setNodeState('step2', 'success', data.time_ms)
    setStepContent('step2', renderMarkdown(data.analysis))
    summary.value.step2 = (data.time_ms / 1000).toFixed(1) + 's'
    showSummary.value = true
  } else {
    setNodeState('step2', 'error')
    setStepContent('step2', `<div style="color:var(--accent)">✗ ${data.error}</div>`)
  }
}

function onStep2Cancel() {
  showPromptModal.value = false
  emit('back')
}

// ── Single-step retry ──
async function retryStep(stepId) {
  emit('update:loading', true)

  try {
    if (stepId === 'step1') {
      await retryStep1()
    } else if (stepId === 'step2') {
      await retryStep2()
    } else if (stepId === 'step3') {
      await retryStep3()
    } else if (stepId === 'step4') {
      await retryStep4()
    } else if (stepId === 'step5') {
      await retryStep5()
    }
    // Clear overall error status if any step succeeds
    if (status.value === 'error') {
      status.value = 'running'
      title.value = '诊断进行中...'
    }
  } catch (e) {
    showInfo('重试失败', e.message)
  } finally {
    emit('update:loading', false)
  }
}

async function retryStep1() {
  setNodeState('step1', 'running')
  focusStep('step1')

  const data = await recognize(props.file)

  if (data.success) {
    context.value.sceneDescription = data.description
    setNodeState('step1', 'success', data.time_ms)
    setStepContent('step1', renderMarkdown(data.description))
    summary.value.step1 = (data.time_ms / 1000).toFixed(1) + 's'
  } else {
    setNodeState('step1', 'error')
    setStepContent('step1', `<div class="md-content" style="color:var(--accent)">✗ ${data.error}</div>`)
    throw new Error(data.error)
  }
}

async function retryStep2() {
  if (!context.value.sceneDescription) {
    showInfo('提示', '缺少场景描述，请先完成步骤 1')
    return
  }

  setNodeState('step2', 'running')
  focusStep('step2')
  // Clear previous children
  nodes.value.step2.children = []
  stepContents.value.step2 = ''
  complianceQueries.value = []

  const data = await analyzeCompliance(context.value.sceneDescription)

  if (data.success) {
    context.value.complianceAnalysis = data.analysis
    setNodeState('step2', 'success', data.time_ms)
    setStepContent('step2', renderMarkdown(data.analysis))
    summary.value.step2 = (data.time_ms / 1000).toFixed(1) + 's'
  } else {
    setNodeState('step2', 'error')
    setStepContent('step2', `<div class="md-content" style="color:var(--accent)">✗ ${data.error}</div>`)
    throw new Error(data.error)
  }
}

async function retryStep3() {
  if (!context.value.sceneDescription || !context.value.complianceAnalysis) {
    showInfo('提示', '缺少前置数据，请先完成步骤 1 和 2')
    return
  }

  setNodeState('step3', 'running')
  focusStep('step3')

  const data = await generatePrompt(context.value.sceneDescription, context.value.complianceAnalysis)

  if (data.success) {
    context.value.editPrompt = data.prompt
    setNodeState('step3', 'success', data.time_ms)
    setStepContent('step3', `<div class="prompt-box">${data.prompt}</div>`)
    summary.value.step3 = (data.time_ms / 1000).toFixed(1) + 's'
  } else {
    setNodeState('step3', 'error')
    setStepContent('step3', `<div class="md-content" style="color:var(--accent)">✗ ${data.error}</div>`)
    throw new Error(data.error)
  }
}

async function retryStep4() {
  if (!context.value.editPrompt) {
    showInfo('提示', '缺少编辑提示词，请先完成步骤 3')
    return
  }

  setNodeState('step4', 'running')
  focusStep('step4')
  step4Images.value = null // 清空旧图，触发扫描动画重置

  const data = await generateImage(props.file, context.value.editPrompt)

  if (data.success) {
    setNodeState('step4', 'success', data.time_ms)
    step4Images.value = {
      original: context.value.originalUrl,
      generated: data.image_url,
    }
    context.value.generatedUrl = data.image_url
    // 保存修改总结
    if (data.summary) {
      editSummary.value = data.summary
    }
    // 激活 Step 5
    setNodeState('step5', 'pending')
    focusStep('step5')
  } else {
    setNodeState('step4', 'error')
    setStepContent('step4', `<div class="md-content" style="color:var(--accent)">✗ ${data.error}</div>`)
    throw new Error(data.error)
  }
}

async function runStep5(userPrompt) {
  if (!context.value.generatedUrl) {
    showInfo('提示', '缺少 Step 4 生成的图片，请先完成步骤 4')
    return
  }

  setNodeState('step5', 'running')
  focusStep('step5')
  step5Images.value = null

  // 将 Step 4 生成的图片 URL 转为 File 对象
  const resp = await fetch(context.value.generatedUrl)
  const blob = await resp.blob()
  const file = new File([blob], 'generated.png', { type: 'image/png' })

  const data = await refineImage(file, userPrompt, context.value.historyId)

  if (data.success) {
    setNodeState('step5', 'success', data.time_ms)
    step5Images.value = {
      original: context.value.generatedUrl,
      generated: data.image_url,
    }
  } else {
    setNodeState('step5', 'error')
    setStepContent('step5', `<div class="md-content" style="color:var(--accent)">✗ ${data.error}</div>`)
  }
}

async function retryStep5() {
  showInfo('提示', '请在输入框中重新输入修正提示词后点击"开始修正"')
  setNodeState('step5', 'pending')
  step5Images.value = null
  focusStep('step5')
}

async function finishFlow() {
  // 跳过 Step 5，直接标记完成
  if (context.value.historyId) {
    try {
      await completeFlow(context.value.historyId)
    } catch (e) {
      console.warn('completeFlow failed:', e)
    }
  }
  setNodeState('step5', 'success')
  status.value = 'done'
  title.value = '诊断完成'
}

onMounted(() => {
  runAnalysis()
})
</script>

<style scoped>
.workspace {
  max-width: 1400px;
  width: 100%;
  height: 100%;
  margin: 0 auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.pipeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--fg);
  margin-bottom: 1.5rem;
  flex-shrink: 0;
}
.pipeline-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.5rem;
  font-weight: 700;
}
.pipeline-status {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.pipeline-status .dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--neutral-400);
}
.pipeline-status .dot.running { background: var(--accent); animation: pulse 1s infinite; }
.pipeline-status .dot.done { background: var(--success); }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.ws-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
  flex: 1;
  overflow: hidden;
}
@media (min-width: 1024px) {
  .ws-layout { grid-template-columns: 340px 1fr; }
}
</style>
