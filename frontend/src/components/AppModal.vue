<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="onCancel" @keydown.escape="onCancel" tabindex="0">
      <div class="modal-box">
        <div class="modal-title">{{ title }}</div>
        <div class="modal-message">{{ message }}</div>
        <input
          v-if="mode === 'prompt'"
          ref="inputRef"
          v-model="inputValue"
          class="modal-input"
          :placeholder="placeholder"
          @keydown.enter="onConfirm"
        >
        <div class="modal-actions">
          <button class="btn btn-outline modal-btn" @click="onCancel">{{ cancelText }}</button>
          <button class="btn btn-primary modal-btn" @click="onConfirm">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  mode: { type: String, default: 'confirm' }, // 'confirm' | 'prompt'
  title: { type: String, default: '提示' },
  message: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  confirmText: { type: String, default: '确认' },
  cancelText: { type: String, default: '取消' },
})

const emit = defineEmits(['confirm', 'cancel'])

const inputValue = ref('')
const inputRef = ref(null)

watch(() => props.visible, (v) => {
  if (v) {
    inputValue.value = ''
    nextTick(() => {
      if (props.mode === 'prompt' && inputRef.value) {
        inputRef.value.focus()
      }
    })
  }
})

function onConfirm() {
  if (props.mode === 'prompt' && !inputValue.value.trim()) return
  emit('confirm', props.mode === 'prompt' ? inputValue.value.trim() : undefined)
}

function onCancel() {
  emit('cancel')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  animation: modalFadeIn 150ms ease;
}

@keyframes modalFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-box {
  background: var(--bg, #F9F9F7);
  border: 2px solid var(--fg, #111);
  padding: 2rem;
  max-width: 440px;
  width: 100%;
  box-shadow: 6px 6px 0px 0px var(--fg, #111);
}

.modal-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
}

.modal-message {
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  color: var(--neutral-600, #525252);
  line-height: 1.6;
  margin-bottom: 1.25rem;
}

.modal-input {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border: 2px solid var(--fg, #111);
  background: var(--bg, #F9F9F7);
  font-family: 'Noto Sans SC', 'Inter', sans-serif;
  font-size: 0.85rem;
  line-height: 1.6;
  margin-bottom: 1.25rem;
  transition: border-color 200ms;
}

.modal-input:focus {
  outline: none;
  border-color: var(--accent, #CC0000);
}

.modal-input::placeholder {
  color: var(--neutral-400, #A3A3A3);
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.modal-btn {
  min-height: 40px;
  padding: 0 1.25rem;
  font-size: 0.6rem;
}
</style>
