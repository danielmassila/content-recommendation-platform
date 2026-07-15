import { apiClient } from './apiClient'

export const ratingsApi = {
  getRatings({ limit = 50 } = {}) {
    return apiClient.get('/api/v1/ratings', { query: { limit } })
  },
  getRatingById(ratingId) {
    return apiClient.get(`/api/v1/ratings/${ratingId}`)
  },
  getUserRatings(userId, { limit = 50 } = {}) {
    return apiClient.get(`/api/v1/users/${userId}/ratings`, { query: { limit } })
  },
  getItemRatings(itemId, { limit = 50 } = {}) {
    return apiClient.get(`/api/v1/items/${itemId}/ratings`, { query: { limit } })
  },
  rateItem(itemId, { userId, grade }) {
    return apiClient.post(`/api/v1/ratings/${itemId}`, { userId, grade })
  },
  updateRating(ratingId, newGrade) {
    return apiClient.put(`/api/v1/ratings/${ratingId}`, null, { query: { newGrade } })
  },
}
