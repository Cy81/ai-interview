<template>
  <div class="admin-dashboard">
    <h1>数据概览</h1>
    <p class="subtitle">欢迎使用管理后台</p>
  </div>
</template>

<script setup>
</script>

<style scoped>
.admin-dashboard {
  padding: var(--space-8) 0;
}
.admin-dashboard h1 {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: 400;
  margin-bottom: var(--space-4);
}
.subtitle {
  color: var(--c-text-muted);
  font-size: var(--text-lg);
}
</style>
