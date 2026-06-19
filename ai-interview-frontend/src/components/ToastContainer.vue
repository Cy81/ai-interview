<template>
  <Teleport to="body">
    <div class="toast-container" aria-live="polite">
      <transition-group name="toast">
        <div
          v-for="t in toastStore.toasts"
          :key="t.id"
          :class="['toast-item', `toast-${t.type}`, { 'toast-leaving': !t.visible }]"
          @click="toastStore.dismiss(t.id)"
        >
          <span class="toast-icon">{{ icons[t.type] }}</span>
          <span class="toast-msg">{{ t.message }}</span>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<script setup>
import { useToastStore } from '../stores/toast'
const toastStore = useToastStore()
const icons = { success: '✓', error: '✕', warning: '!', info: 'i' }
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: var(--space-5);
  right: var(--space-5);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  pointer-events: none;
}
.toast-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: 500;
  box-shadow: var(--shadow-md);
  pointer-events: auto;
  cursor: pointer;
  max-width: 380px;
  border-left: 3px solid transparent;
}
.toast-success {
  background: var(--c-success-light);
  color: var(--c-success);
  border-left-color: var(--c-success);
}
.toast-error {
  background: var(--c-danger-light);
  color: var(--c-danger);
  border-left-color: var(--c-danger);
}
.toast-warning {
  background: var(--c-warning-light);
  color: var(--c-warning);
  border-left-color: var(--c-warning);
}
.toast-info {
  background: var(--c-primary-light);
  color: var(--c-primary);
  border-left-color: var(--c-primary);
}
.toast-icon {
  width: 20px; height: 20px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 800;
  flex-shrink: 0;
}
.toast-success .toast-icon { background: var(--c-success); color: white; }
.toast-error .toast-icon { background: var(--c-danger); color: white; }
.toast-warning .toast-icon { background: var(--c-warning); color: white; }
.toast-info .toast-icon { background: var(--c-primary); color: white; }
.toast-msg { line-height: 1.45; }

.toast-enter-active { transition: all 0.35s var(--ease-out); }
.toast-leave-active { transition: all 0.25s ease-in; }
.toast-enter-from { opacity: 0; transform: translateX(40px) scale(0.95); }
.toast-leave-to { opacity: 0; transform: translateX(40px) scale(0.95); }
.toast-move { transition: transform 0.3s ease; }
</style>
