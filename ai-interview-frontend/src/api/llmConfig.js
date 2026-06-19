import adminApi from './adminRequest'

// ---- Provider API ----

export function listProviders() {
  return adminApi.get('/llm-configs')
}

export function createProvider(data) {
  return adminApi.post('/llm-configs', data)
}

export function updateProvider(id, data) {
  return adminApi.put(`/llm-configs/${id}`, data)
}

export function deleteProvider(id) {
  return adminApi.delete(`/llm-configs/${id}`)
}

// ---- Model API ----

export function addModel(providerId, data) {
  return adminApi.post(`/llm-configs/${providerId}/models`, data)
}

export function updateModel(id, data) {
  return adminApi.put(`/llm-configs/models/${id}`, data)
}

export function deleteModel(id) {
  return adminApi.delete(`/llm-configs/models/${id}`)
}

export function activateModel(id) {
  return adminApi.put(`/llm-configs/models/${id}/activate`)
}

// ---- Test API ----

export function testConfig(data) {
  return adminApi.post('/llm-configs/test', data)
}
