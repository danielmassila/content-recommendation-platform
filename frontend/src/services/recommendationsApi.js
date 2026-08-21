import { apiClient } from './apiClient'

export const recommendationsApi = {
  getAdminRecommendations({ limit = 10, includeReason = false } = {}) {
    return apiClient.get('/api/v1/admin/recommendations', {
      query: { limit, includeReason },
    })
  },
  getCurrentUserRecommendations({ limit = 20, includeReason = false, algo } = {}) {
    return apiClient.get('/api/v1/me/recommendations', {
      query: { limit, includeReason, algo },
    })
  },
  recomputeCurrentUserRecommendations({ limit = 20, includeReason = false, algo } = {}) {
    return apiClient.post('/api/v1/me/recommendations/recompute', null, {
      query: { limit, includeReason, algo },
    })
  },
  recomputeAllRecommendations() {
    return apiClient.post('/api/v1/admin/recommendations/recompute')
  },
}
