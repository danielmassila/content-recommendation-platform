import { apiClient } from './apiClient'

export const usersApi = {
  getUsers({ limit = 50 } = {}) {
    return apiClient.get('/api/v1/users', { query: { limit } })
  },
  getCurrentUser() {
    return apiClient.get('/api/v1/me')
  },
  createUser({ email }) {
    return apiClient.post('/api/v1/users', { email })
  },
  updateCurrentUser({ email, username }) {
    return apiClient.put('/api/v1/me', { email, username })
  },
  changeCurrentUserPassword({ currentPassword, newPassword }) {
    return apiClient.put('/api/v1/me/password', {
      currentPassword,
      newPassword,
    })
  },
}
