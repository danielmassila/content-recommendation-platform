import { apiClient } from './apiClient'

export const authApi = {
  login({ email, password }) {
    return apiClient.post('/api/v1/auth/login', { email, password })
  },
  register({ email, password, username }) {
    return apiClient.post('/api/v1/auth/register', { email, password, username })
  },
  getCurrentUser() {
    return apiClient.get('/api/v1/me')
  },
}
