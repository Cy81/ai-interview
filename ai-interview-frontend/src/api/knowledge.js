import adminApi from './adminRequest'

export const knowledgeApi = {
  listDocuments: (params) => adminApi.get('/knowledge/documents', { params }),
  uploadDocument: (formData) => adminApi.post('/knowledge/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getDocument: (id) => adminApi.get(`/knowledge/documents/${id}`),
  deleteDocument: (id) => adminApi.delete(`/knowledge/documents/${id}`),
  toggleDocument: (id, data) => adminApi.patch(`/knowledge/documents/${id}/toggle`, data),
  reindexDocument: (id) => adminApi.post(`/knowledge/documents/${id}/reindex`),
  listChunks: (id, params) => adminApi.get(`/knowledge/documents/${id}/chunks`, { params }),
  testRetrieve: (data) => adminApi.post('/knowledge/test-retrieve', data)
}
