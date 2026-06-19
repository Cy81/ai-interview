/**
 * 通用工具函数
 */

/**
 * 格式化日期
 * @param {string} str - ISO 日期字符串
 * @param {object} options - Intl.DateTimeFormat 选项
 * @returns {string}
 */
export function formatDate(str, options) {
  if (!str) return ''
  const defaults = { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }
  return new Date(str).toLocaleString('zh-CN', options || defaults)
}

/**
 * 格式化完整日期时间
 */
export function formatDateTime(str) {
  if (!str) return ''
  return new Date(str).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

/**
 * 根据分数返回颜色
 * @param {number} score - 0-10 分
 * @returns {string} hex color
 */
export function scoreColor(score) {
  if (score >= 8) return '#059669'
  if (score >= 6) return '#d97706'
  return '#dc2626'
}

/**
 * 根据分数返回颜色 CSS 变量名
 */
export function scoreColorVar(score) {
  if (score >= 8) return 'var(--c-success)'
  if (score >= 6) return 'var(--c-warning)'
  return 'var(--c-danger)'
}

/**
 * 难度映射
 */
export const difficultyMap = { easy: '简单', medium: '中等', hard: '困难' }

/**
 * 简单 HTML 转义（防止 XSS）
 */
export function escapeHtml(str) {
  if (!str) return ''
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

/**
 * 防抖
 */
export function debounce(fn, delay = 300) {
  let timer
  return function (...args) {
    clearTimeout(timer)
    timer = setTimeout(() => fn.apply(this, args), delay)
  }
}

/**
 * 确认弹窗（替代 window.confirm）
 * 返回 Promise<boolean>
 */
export function useConfirm(toastStore) {
  return (message) => {
    return new Promise(resolve => {
      resolve(confirm(message))
    })
  }
}
