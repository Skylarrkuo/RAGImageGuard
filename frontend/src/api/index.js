const API_BASE = ''

/**
 * 检查配置
 */
export async function checkConfig() {
  const resp = await fetch(`${API_BASE}/api/config-check`)
  return resp.json()
}

/**
 * Step 1: 识别图片
 */
export async function recognize(image) {
  const formData = new FormData()
  formData.append('image', image)
  const resp = await fetch(`${API_BASE}/api/recognize`, { method: 'POST', body: formData })
  return resp.json()
}

/**
 * Step 2: 合规分析
 */
export async function analyzeCompliance(sceneDescription, userRole = 'tourist') {
  const formData = new FormData()
  formData.append('scene_description', sceneDescription)
  formData.append('user_role', userRole)
  const resp = await fetch(`${API_BASE}/api/analyze-compliance`, { method: 'POST', body: formData })
  return resp.json()
}

/**
 * Step 3: 生成提示词
 */
export async function generatePrompt(sceneDescription, complianceAnalysis) {
  const formData = new FormData()
  formData.append('scene_description', sceneDescription)
  formData.append('compliance_analysis', complianceAnalysis)
  const resp = await fetch(`${API_BASE}/api/generate-prompt`, { method: 'POST', body: formData })
  return resp.json()
}

/**
 * Step 4: 图片编辑
 */
export async function generateImage(image, prompt) {
  const formData = new FormData()
  formData.append('image', image)
  formData.append('prompt', prompt)
  const resp = await fetch(`${API_BASE}/api/generate-image`, { method: 'POST', body: formData })
  return resp.json()
}

/**
 * Step 5: 补充编辑
 */
export async function refineImage(image, prompt, historyId) {
  const formData = new FormData()
  formData.append('image', image)
  formData.append('prompt', prompt)
  if (historyId) formData.append('history_id', historyId)
  const resp = await fetch(`${API_BASE}/api/refine-image`, { method: 'POST', body: formData })
  return resp.json()
}

/**
 * 结束流程（跳过 Step 5）
 */
export async function completeFlow(historyId) {
  const formData = new FormData()
  formData.append('history_id', historyId)
  const resp = await fetch(`${API_BASE}/api/complete-flow`, { method: 'POST', body: formData })
  return resp.json()
}

/**
 * SSE 流式完整流水线
 * 返回 ReadableStream reader，调用方自行解析 SSE 事件
 */
export async function fullPipelineStream(image) {
  const formData = new FormData()
  formData.append('image', image)
  const resp = await fetch(`${API_BASE}/api/full-pipeline-stream`, { method: 'POST', body: formData })
  if (!resp.ok) throw new Error(resp.statusText)
  return resp.body.getReader()
}

/**
 * 解析 SSE 流，逐条回调
 */
export async function consumeSSEStream(reader, onEvent) {
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data:')) continue
      try {
        const ev = JSON.parse(line.slice(5).trim())
        onEvent(ev)
      } catch { /* ignore parse errors */ }
    }
  }
}

/**
 * 历史记录 API
 */
export async function getHistory() {
  const resp = await fetch(`${API_BASE}/api/history`)
  return resp.json()
}

export async function getHistoryDetail(id) {
  const resp = await fetch(`${API_BASE}/api/history/${id}`)
  return resp.json()
}

export async function deleteHistory(id) {
  const resp = await fetch(`${API_BASE}/api/history/${id}`, { method: 'DELETE' })
  return resp.json()
}
