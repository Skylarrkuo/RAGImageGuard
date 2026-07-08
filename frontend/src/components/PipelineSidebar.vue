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
          @click="$emit('toggle-compliance', child.index)"
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

defineEmits(['focus', 'retry', 'toggle-compliance'])
</script>

<style scoped>
.pipeline-sidebar {
  border: 1px solid var(--fg);
  background: var(--bg);
  overflow-y: auto;
}
.pipeline-sidebar-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--fg);
  background: var(--fg);
  color: var(--bg);
}

.node {
  border-bottom: 1px solid var(--muted);
  transition: background 200ms;
}
.node:last-child { border-bottom: none; }
.node:hover { background: var(--neutral-100); }
.node.active { background: rgba(204,0,0,0.03); }

.node-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
}

.node-icon {
  width: 28px; height: 28px;
  border: 1px solid var(--muted);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 500;
  transition: all 200ms;
}
.node.running .node-icon {
  border-color: var(--accent);
  color: var(--accent);
  animation: pulse 1s infinite;
}
.node.success .node-icon {
  border-color: var(--success);
  background: var(--success);
  color: #fff;
}
.node.error .node-icon {
  border-color: var(--accent);
  background: var(--accent);
  color: #fff;
}

.node-info { flex: 1; min-width: 0; }
.node-title {
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  font-weight: 600;
}
.node-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.55rem;
  color: var(--neutral-500);
  margin-top: 0.1rem;
}

.node-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border: 1px solid var(--muted);
  color: var(--neutral-500);
}
.node.running .node-badge { border-color: var(--accent); color: var(--accent); }
.node.success .node-badge { border-color: var(--success); color: var(--success); }
.node.error .node-badge { border-color: var(--accent); color: var(--accent); }

.node-retry-btn {
  font-family: 'Inter', sans-serif;
  font-size: 0.5rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  transition: all 200ms;
  flex-shrink: 0;
}
.node-retry-btn:hover {
  background: var(--accent);
  color: #fff;
}
.node-retry-btn svg {
  stroke: currentColor;
}

.node-children {
  display: none;
  padding: 0 1rem 0.5rem 2.5rem;
}
.node.active .node-children { display: block; }

.child-node {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.4rem 0;
  border-left: 1px solid var(--muted);
  padding-left: 0.75rem;
  margin-left: 0.35rem;
  cursor: pointer;
  transition: color 200ms;
}
.child-node:hover .child-node-text { color: var(--fg); }
.child-dot {
  width: 6px; height: 6px;
  border: 1px solid var(--neutral-400);
  flex-shrink: 0;
  margin-top: 0.35rem;
  transition: all 200ms;
}
.child-node.running .child-dot {
  border-color: var(--accent);
  background: var(--accent);
  animation: pulse 1s infinite;
}
.child-node.success .child-dot {
  border-color: var(--success);
  background: var(--success);
}
.child-node-text {
  font-family: 'Inter', sans-serif;
  font-size: 0.7rem;
  color: var(--neutral-600);
  line-height: 1.5;
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
</style>
