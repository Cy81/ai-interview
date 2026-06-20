<template>
  <div class="container">
    <div class="welcome-section">
      <h1>欢迎使用</h1>
      <p class="subtitle">您已成功登录，这是您的仪表盘。</p>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.welcome-section {
  text-align: center;
  padding: var(--space-16) 0;
}
.welcome-section h1 {
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
