<template>
  <div class="auth-page">
    <div class="auth-brand">
      <div class="auth-brand-content">
        <div class="auth-brand-logo">智面</div>
        <p class="auth-brand-tagline">AI 驱动的模拟面试，让你在真实场景中脱颖而出</p>
        <div class="auth-brand-features">
          <div class="auth-brand-feature">
            <span class="auth-brand-feature-dot"></span>
            <span>智能简历解析与岗位匹配</span>
          </div>
          <div class="auth-brand-feature">
            <span class="auth-brand-feature-dot"></span>
            <span>多轮对话式真实面试模拟</span>
          </div>
          <div class="auth-brand-feature">
            <span class="auth-brand-feature-dot"></span>
            <span>专业评估报告与改进建议</span>
          </div>
        </div>
      </div>
    </div>
    <div class="auth-form-panel">
      <div class="auth-card">
        <h2><slot name="title">欢迎回来</slot></h2>
        <p class="subtitle"><slot name="subtitle">登录你的智面账号</slot></p>
        <slot></slot>
        <div class="auth-footer">
          <slot name="footer"></slot>
        </div>
      </div>
    </div>
  </div>
</template>
