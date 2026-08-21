import { apiClient } from './apiClient'

export const preferencesApi = {
  getCurrentUserPreferences() {
    return apiClient.get('/api/v1/me/preferences')
  },
  replaceCurrentUserPreferences(entries) {
    return apiClient.put('/api/v1/me/preferences', { entries })
  },
}
