import { apiClient } from './apiClient'

export const recommendationsApi = {
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
}
