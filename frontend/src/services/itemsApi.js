import { apiClient } from './apiClient'

export const itemsApi = {
  getItems({ page = 0, query = '', size = 20, type = 'MOVIE' } = {}) {
    return apiClient.get('/api/v1/items', { query: { page, query, size, type } })
  },
  getItemById(itemId) {
    return apiClient.get(`/api/v1/items/${itemId}`)
  },
  createItem({ title, type = 'MOVIE', metadata }) {
    return apiClient.post('/api/v1/items', { title, type, metadata })
  },
}
