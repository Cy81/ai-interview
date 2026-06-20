import adminApi from './adminRequest'

export function listLogs(params) {
  return adminApi.get('/llm-logs', { params })
}

export function getLogDetail(id) {
  return adminApi.get(`/llm-logs/${id}`)
}

export function getTokenStats(params) {
  return adminApi.get('/llm-logs/stats', { params })
}

export function getCostEstimate(params) {
  return adminApi.get('/llm-logs/cost-estimate', { params })
}

export function getEvaluationMetrics(params) {
  return adminApi.get('/llm-logs/evaluation', { params })
}
