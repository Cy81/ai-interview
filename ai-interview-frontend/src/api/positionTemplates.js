import api from './request'

export function getPositionTemplates() {
  return api.get('/position-templates')
}
