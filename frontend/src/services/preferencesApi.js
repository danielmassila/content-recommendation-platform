import { apiClient } from './apiClient'

export const preferencesApi = {
  getUserPreferences(userId) {
    return apiClient.get(`/api/v1/users/${userId}/preferences`)
  },
  replaceUserPreferences(userId, entries) {
    return apiClient.put(`/api/v1/users/${userId}/preferences`, { entries })
  },
}
