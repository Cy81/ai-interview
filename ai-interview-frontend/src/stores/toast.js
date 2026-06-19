import { defineStore } from 'pinia'
import { ref } from 'vue'

let nextId = 0

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function show(message, type = 'info', duration = 3000) {
    const id = ++nextId
    toasts.value.push({ id, message, type, visible: true })
    if (duration > 0) {
      setTimeout(() => dismiss(id), duration)
    }
    return id
  }

  function success(msg, duration) { return show(msg, 'success', duration) }
  function error(msg, duration = 5000) { return show(msg, 'error', duration) }
  function warning(msg, duration) { return show(msg, 'warning', duration) }

  function dismiss(id) {
    const t = toasts.value.find(t => t.id === id)
    if (t) t.visible = false
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, 300)
  }

  return { toasts, show, success, error, warning, dismiss }
})
