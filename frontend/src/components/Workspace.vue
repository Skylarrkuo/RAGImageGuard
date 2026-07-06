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
        />

        <!-- Content Panel -->
        <ContentPanel
          :title="panelTitle"
          :time="panelTime"
          :content="panelContent"
          :loading="panelLoading"
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import { recognize, analyzeCompliance, generatePrompt, fullPipelineStream, consumeSSEStream } from '../api/index.js'
import PipelineSidebar from './PipelineSidebar.vue'
import ContentPanel from './ContentPanel.vue'
import SummaryBar from './SummaryBar.vue'

const props = defineProps({
  file: { type: File, required: true },
  mode: { type: String, default: 'full' },
})

const emit = defineEmits(['back', 'update:loading'])

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
})

// Content for each step
const stepContents = ref({})

// Intermediate results for retry support
const context = ref({
  sceneDescription: null,
  complianceAnalysis: null,
  editPrompt: null,
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
  }
  return titles[currentStep.value] || '等待开始'
})

const panelContent = computed(() => {
  const raw = stepContents.value[currentStep.value]
  if (!raw) return '<div class="content-empty">等待数据...</div>'
  // step2 stores raw markdown; others store pre-rendered HTML
  if (currentStep.value === 'step2') {
    return renderMarkdown(raw)
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
    alert('分析失败: ' + e.message)
  } finally {
    emit('update:loading', false)
    // Check if any node has error state
    const hasError = Object.values(nodes.value).some(n => n.state === 'error')
    if (hasError) {
      status.value = 'error'
      title.value = '诊断出错 — 可点击重试失败步骤'
    } else {
      status.value = 'done'
      title.value = '诊断完成'
    }
  }
}

async function runFullPipeline() {
  const reader = await fullPipelineStream(props.file)

  await consumeSSEStream(reader, (ev) => {
    // Step events
    if (ev.type === 'step') {
      const stepMap = { recognize: 'step1', compliance: 'step2', prompt: 'step3', image_edit: 'step4' }
      const stepId = stepMap[ev.step]

      if (ev.status === 'running') {
        setNodeState(stepId, 'running')
        focusStep(stepId)
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
          } else if (stepId === 'step3') {
            context.value.editPrompt = ev.prompt
            setStepContent(stepId, `<div class="prompt-box">${ev.prompt}</div>`)
          } else if (stepId === 'step4') {
            if (ev.success && ev.image_url) {
              setStepContent(stepId, `<div class="generated-wrap"><img src="${ev.image_url}" alt="Generated"></div>`)
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

      // Add query divider (will be wrapped by renderMarkdown later via marked's sanitize)
      const divider = ev.index > 0 ? '\n\n---\n\n' : ''
      stepContents.value.step2 = (stepContents.value.step2 || '') + `${divider}### 问题 ${ev.index + 1}\n*${ev.question}*\n\n`
    }

    // Compliance chunk (streaming content)
    if (ev.type === 'compliance_chunk') {
      appendStepStream('step2', ev.text)
    }

    // Query end
    if (ev.type === 'query_end') {
      const child = nodes.value.step2.children.find(c => c.id === `child-${ev.index}`)
      if (child) child.state = 'success'
    }

    // Done
    if (ev.type === 'done') {
      const totalMs = ev.total_time_ms
      summary.value.total = (totalMs / 1000).toFixed(1) + 's'
      showSummary.value = true
      panelTime.value = (totalMs / 1000).toFixed(1) + 's'
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
  const desc = prompt('请输入场景描述：')
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
    }
    // Clear overall error status if any step succeeds
    if (status.value === 'error') {
      status.value = 'running'
      title.value = '诊断进行中...'
    }
  } catch (e) {
    alert('重试失败: ' + e.message)
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
    alert('缺少场景描述，请先完成步骤 1')
    return
  }

  setNodeState('step2', 'running')
  focusStep('step2')
  // Clear previous children
  nodes.value.step2.children = []
  stepContents.value.step2 = ''

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
    alert('缺少前置数据，请先完成步骤 1 和 2')
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
    alert('缺少编辑提示词，请先完成步骤 3')
    return
  }

  setNodeState('step4', 'running')
  focusStep('step4')

  const { generateImage } = await import('../api/index.js')
  const data = await generateImage(props.file, context.value.editPrompt)

  if (data.success) {
    setNodeState('step4', 'success', data.time_ms)
    setStepContent('step4', `<div class="generated-wrap"><img src="${data.image_url}" alt="Generated"></div>`)
  } else {
    setNodeState('step4', 'error')
    setStepContent('step4', `<div class="md-content" style="color:var(--accent)">✗ ${data.error}</div>`)
    throw new Error(data.error)
  }
}

onMounted(() => {
  runAnalysis()
})
</script>
