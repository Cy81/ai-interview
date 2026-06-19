import adminApi from './adminRequest'

export const positionTemplateApi = {
  list: (params) => adminApi.get('/position-templates', { params }),
  create: (data) => adminApi.post('/position-templates', data),
  get: (id) => adminApi.get(`/position-templates/${id}`),
  update: (id, data) => adminApi.put(`/position-templates/${id}`, data),
  delete: (id) => adminApi.delete(`/position-templates/${id}`),
  toggle: (id, data) => adminApi.patch(`/position-templates/${id}/toggle`, data)
}
