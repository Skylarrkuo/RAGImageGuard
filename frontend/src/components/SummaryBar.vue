<template>
  <div class="summary-bar">
    <div class="summary-item">
      <div class="summary-item-label">Step 01</div>
      <div class="summary-item-value">{{ step1 }}</div>
    </div>
    <div class="summary-item">
      <div class="summary-item-label">Step 02</div>
      <div class="summary-item-value">{{ step2 }}</div>
    </div>
    <div class="summary-item">
      <div class="summary-item-label">Step 03</div>
      <div class="summary-item-value">{{ step3 }}</div>
    </div>
    <div class="summary-item">
      <div class="summary-item-label">Total</div>
      <div class="summary-item-value">{{ total }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  step1: { type: String, default: '—' },
  step2: { type: String, default: '—' },
  step3: { type: String, default: '—' },
  total: { type: String, default: '—' },
})
</script>

<style scoped>
.summary-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--fg);
  margin-top: 1.5rem;
}
.summary-item {
  padding: 1rem;
  border-right: 1px solid var(--fg);
  text-align: center;
}
.summary-item:last-child { border-right: none; }
.summary-item-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--neutral-500);
  margin-bottom: 0.25rem;
}
.summary-item-value {
  font-family: 'Playfair Display', serif;
  font-size: 1.5rem;
  font-weight: 700;
}
</style>
