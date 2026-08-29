import { apiClient } from './apiClient'

export const itemsApi = {
  getItems({ genre = '', minVote = '', page = 0, query = '', ratingStatus = 'all', size = 20, type = 'MOVIE', year = '' } = {}) {
    return apiClient.get('/api/v1/items', {
      query: { genre, minVote, page, query, ratingStatus, size, type, year },
    })
  },
  getItemById(itemId) {
    return apiClient.get(`/api/v1/items/${itemId}`)
  },
}
