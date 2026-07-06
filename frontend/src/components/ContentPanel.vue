<template>
  <div class="content-panel">
    <div class="content-panel-header">
      <span>{{ title }}</span>
      <span>{{ time }}</span>
    </div>
    <div class="content-panel-body" ref="bodyRef">
      <div v-if="loading && !hasContent" class="content-loading">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div class="loading-text">正在生成</div>
      </div>
      <div v-else-if="loading && hasContent" class="content-streaming" v-html="content">
      </div>
      <div v-else v-html="content"></div>
      <!-- Streaming cursor -->
      <span v-if="loading && hasContent" class="streaming-cursor"></span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '等待开始' },
  time: { type: String, default: '' },
  content: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})

const bodyRef = ref(null)

const hasContent = computed(() => {
  return props.content && !props.content.includes('content-empty')
})

// Auto-scroll to bottom when content changes
watch(() => props.content, async () => {
  await nextTick()
  if (bodyRef.value) {
    bodyRef.value.scrollTop = bodyRef.value.scrollHeight
  }
})
</script>
