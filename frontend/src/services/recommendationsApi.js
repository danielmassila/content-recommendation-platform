import { apiClient } from './apiClient'

export const recommendationsApi = {
  getAdminRecommendations({ limit = 10, includeReason = false } = {}) {
    return apiClient.get('/api/v1/admin/recommendations', {
      query: { limit, includeReason },
    })
  },
  getUserRecommendations(userId, { limit = 20, includeReason = false, algo } = {}) {
    return apiClient.get(`/api/v1/users/${userId}/recommendations`, {
      query: { limit, includeReason, algo },
    })
  },
  recomputeUserRecommendations(userId, { limit = 20, includeReason = false, algo } = {}) {
    return apiClient.post(`/api/v1/users/${userId}/recommendations/recompute`, null, {
      query: { limit, includeReason, algo },
    })
  },
  recomputeAllRecommendations() {
    return apiClient.post('/api/v1/admin/recommendations/recompute')
  },
}
