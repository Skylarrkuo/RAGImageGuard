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
