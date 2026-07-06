<template>
  <div class="pipeline-sidebar">
    <div class="pipeline-sidebar-title">Pipeline Nodes</div>

    <div
      v-for="(node, stepId) in nodes"
      :key="stepId"
      class="node"
      :class="[node.state, { active: activeStep === stepId }]"
    >
      <div class="node-header" @click="$emit('focus', stepId)">
        <div class="node-icon">{{ stepId.replace('step', '').padStart(2, '0') }}</div>
        <div class="node-info">
          <div class="node-title">{{ node.label }}</div>
          <div class="node-time">{{ node.timeMs ? (node.timeMs / 1000).toFixed(1) + 's' : '—' }}</div>
        </div>
        <button
          v-if="node.state === 'error'"
          class="node-retry-btn"
          title="重试此步骤"
          @click.stop="$emit('retry', stepId)"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          重试
        </button>
        <div v-else class="node-badge">{{ node.badge }}</div>
      </div>

      <!-- Children (sub-queries for step2) -->
      <div v-if="node.children && node.children.length > 0" class="node-children">
        <div
          v-for="child in node.children"
          :key="child.id"
          class="child-node"
          :class="child.state"
        >
          <div class="child-dot"></div>
          <div class="child-node-text">Q{{ child.index + 1 }}: {{ child.question }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  nodes: { type: Object, required: true },
  activeStep: { type: String, default: '' },
})

defineEmits(['focus', 'retry'])
</script>
