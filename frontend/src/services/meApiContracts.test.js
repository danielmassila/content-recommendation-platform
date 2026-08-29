import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from './apiClient'
import { preferencesApi } from './preferencesApi'
import { ratingsApi } from './ratingsApi'
import { recommendationsApi } from './recommendationsApi'
import { usersApi } from './usersApi'

describe('current-user API contracts', () => {
  beforeEach(() => {
    vi.spyOn(apiClient, 'get').mockResolvedValue([])
    vi.spyOn(apiClient, 'put').mockResolvedValue({})
    vi.spyOn(apiClient, 'post').mockResolvedValue([])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('never accepts a user identifier for personal resources', async () => {
    await usersApi.getCurrentUser()
    await ratingsApi.getCurrentUserRatings({ limit: 10 })
    await preferencesApi.getCurrentUserPreferences()
    await recommendationsApi.getCurrentUserRecommendations({ limit: 20 })

    expect(apiClient.get).toHaveBeenNthCalledWith(1, '/api/v1/me')
    expect(apiClient.get).toHaveBeenNthCalledWith(2, '/api/v1/me/ratings', { query: { limit: 10 } })
    expect(apiClient.get).toHaveBeenNthCalledWith(3, '/api/v1/me/preferences')
    expect(apiClient.get).toHaveBeenNthCalledWith(4, '/api/v1/me/recommendations', {
      query: { algo: undefined, includeReason: false, limit: 20 },
    })
  })

  it('rates an item through the authenticated-user endpoint', async () => {
    await ratingsApi.rateItem(42, 4)

    expect(apiClient.put).toHaveBeenCalledWith('/api/v1/me/ratings/42', { grade: 4 })
  })
})
