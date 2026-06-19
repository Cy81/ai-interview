import adminApi from './adminRequest'

export const adminUserApi = {
  list: (params) => adminApi.get('/users', { params }),
  stats: () => adminApi.get('/users/stats'),
  toggleActive: (id) => adminApi.put(`/users/${id}/toggle-active`)
}

export const adminInterviewApi = {
  list: (params) => adminApi.get('/interviews', { params }),
  detail: (id) => adminApi.get(`/interviews/${id}`),
  delete: (id) => adminApi.delete(`/interviews/${id}`)
}
