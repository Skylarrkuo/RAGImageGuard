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
