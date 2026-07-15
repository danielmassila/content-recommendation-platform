import { apiClient } from './apiClient'

export const usersApi = {
  getUsers({ limit = 50 } = {}) {
    return apiClient.get('/api/v1/users', { query: { limit } })
  },
  getUserById(userId) {
    return apiClient.get(`/api/v1/users/${userId}`)
  },
  createUser({ email }) {
    return apiClient.post('/api/v1/users', { email })
  },
}
