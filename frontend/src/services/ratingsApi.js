import { apiClient } from './apiClient'

export const ratingsApi = {
  getRatings({ limit = 50 } = {}) {
    return apiClient.get('/api/v1/ratings', { query: { limit } })
  },
  getRatingById(ratingId) {
    return apiClient.get(`/api/v1/ratings/${ratingId}`)
  },
  getCurrentUserRatings({ limit = 50 } = {}) {
    return apiClient.get('/api/v1/me/ratings', { query: { limit } })
  },
  getItemRatings(itemId, { limit = 50 } = {}) {
    return apiClient.get(`/api/v1/items/${itemId}/ratings`, { query: { limit } })
  },
  rateItem(itemId, grade) {
    return apiClient.put(`/api/v1/me/ratings/${itemId}`, { grade })
  },
}
