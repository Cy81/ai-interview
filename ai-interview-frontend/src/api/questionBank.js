import adminApi from './adminRequest'

export const questionBankApi = {
  list: (params) => adminApi.get('/question-bank', { params }),
  stats: () => adminApi.get('/question-bank/stats'),
  create: (data) => adminApi.post('/question-bank', data),
  get: (id) => adminApi.get(`/question-bank/${id}`),
  update: (id, data) => adminApi.put(`/question-bank/${id}`, data),
  delete: (id) => adminApi.delete(`/question-bank/${id}`),
  toggle: (id, data) => adminApi.patch(`/question-bank/${id}/toggle`, data),
  batchImport: (data) => adminApi.post('/question-bank/batch-import', data),
  reindexAll: () => adminApi.post('/question-bank/reindex-all'),
  testRetrieve: (data) => adminApi.post('/question-bank/test-retrieve', data)
}
