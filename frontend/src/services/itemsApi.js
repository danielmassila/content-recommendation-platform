import { apiClient } from './apiClient'

export const itemsApi = {
  getItems({ limit = 50 } = {}) {
    return apiClient.get('/api/v1/items', { query: { limit } })
  },
  getItemById(itemId) {
    return apiClient.get(`/api/v1/items/${itemId}`)
  },
  createItem({ title, type = 'MOVIE', metadata }) {
    return apiClient.post('/api/v1/items', { title, type, metadata })
  },
}
