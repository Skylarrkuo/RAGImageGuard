<template>
  <div class="loading-bar" :class="{ active: loading }"></div>

  <!-- Header -->
  <header class="header">
    <div class="header-inner">
      <div class="header-brand">AI 景区合规诊断</div>
      <div class="header-meta">Workstation · Vol 1.0</div>
    </div>
  </header>

  <!-- Upload Page -->
  <UploadPage
    v-if="currentPage === 'upload'"
    @start="handleStart"
    @show-history="currentPage = 'history'"
  />

  <!-- Workspace Page -->
  <Workspace
    v-if="currentPage === 'workspace'"
    :file="selectedFile"
    :mode="currentMode"
    @back="goBack"
    @update:loading="loading = $event"
  />

  <!-- History Page -->
  <HistoryPage
    v-if="currentPage === 'history'"
    @back="currentPage = 'upload'"
  />

  <!-- Footer (上传页显示，工作台隐藏以节省空间) -->
  <footer v-if="currentPage === 'upload'" class="footer">
    <div class="footer-text">景区合规智能诊断系统 · AI Visual Diagnosis Workstation</div>
  </footer>
</template>

<script setup>
import { ref } from 'vue'
import UploadPage from './components/UploadPage.vue'
import Workspace from './components/Workspace.vue'
import HistoryPage from './components/HistoryPage.vue'

const currentPage = ref('upload')
const selectedFile = ref(null)
const currentMode = ref('full')
const loading = ref(false)

function handleStart({ file, mode }) {
  selectedFile.value = file
  currentMode.value = mode
  currentPage.value = 'workspace'
}

function goBack() {
  currentPage.value = 'upload'
  selectedFile.value = null
}
</script>

<style scoped>
.loading-bar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--fg);
  z-index: 100;
  overflow: hidden;
  display: none;
}
.loading-bar.active { display: block; }
.loading-bar::after {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--accent);
  animation: loadSlide 1.2s ease-in-out infinite;
  transform-origin: left;
}
@keyframes loadSlide {
  0% { transform: translateX(-100%) scaleX(0.4); }
  50% { transform: translateX(0%) scaleX(0.3); }
  100% { transform: translateX(100%) scaleX(0.4); }
}
</style>
