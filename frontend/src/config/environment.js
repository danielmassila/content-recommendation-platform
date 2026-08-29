const DEFAULT_API_BASE_URL = 'http://localhost:8081'

const parseHttpUrl = (value) => {
  try {
    const url = new URL(value)
    if (!['http:', 'https:'].includes(url.protocol)) {
      throw new Error('unsupported protocol')
    }
    return url.origin
  } catch {
    throw new Error('VITE_API_BASE_URL must be a valid HTTP(S) URL')
  }
}

export const getEnvironment = () => ({
  apiBaseUrl: parseHttpUrl(import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL),
})
