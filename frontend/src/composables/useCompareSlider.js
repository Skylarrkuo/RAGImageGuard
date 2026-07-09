import { ref } from 'vue'

/**
 * 图片对比滑块拖拽逻辑
 * @param {import('vue').Ref<HTMLElement|null>} containerRef - 滑块容器元素 ref
 * @returns {{ sliderPos: import('vue').Ref<number>, isDragging: import('vue').Ref<boolean>, startDrag: (e: Event) => void }}
 */
export function useCompareSlider(containerRef) {
  const sliderPos = ref(50)
  const isDragging = ref(false)

  function updateSlider(e) {
    if (!containerRef.value) return
    const rect = containerRef.value.getBoundingClientRect()
    const touch = e.touches ? e.touches[0] : e
    const x = touch.clientX - rect.left
    sliderPos.value = Math.max(0, Math.min(100, (x / rect.width) * 100))
  }

  function onDrag(e) {
    if (!isDragging.value) return
    e.preventDefault()
    updateSlider(e)
  }

  function stopDrag() {
    isDragging.value = false
    window.removeEventListener('mousemove', onDrag)
    window.removeEventListener('touchmove', onDrag)
    window.removeEventListener('mouseup', stopDrag)
    window.removeEventListener('touchend', stopDrag)
  }

  function startDrag(e) {
    isDragging.value = true
    updateSlider(e)
    window.addEventListener('mousemove', onDrag)
    window.addEventListener('touchmove', onDrag, { passive: false })
    window.addEventListener('mouseup', stopDrag)
    window.addEventListener('touchend', stopDrag)
  }

  return { sliderPos, isDragging, startDrag }
}
