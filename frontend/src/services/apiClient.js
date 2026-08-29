import { getEnvironment } from '../config/environment'

let accessToken = null
let unauthorizedHandler = null

export class ApiError extends Error {
  constructor(message, { code, status } = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

export const setApiAccessToken = (token) => {
  accessToken = token
}

export const setUnauthorizedHandler = (handler) => {
  unauthorizedHandler = handler
}

const getApiBaseUrl = () => {
  return getEnvironment().apiBaseUrl
}

const buildUrl = (path, query) => {
  const url = new URL(path, getApiBaseUrl())

  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value)
    }
  })

  return url
}

const parseResponse = async (response) => {
  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type')
  const payload = contentType?.includes('json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message =
      typeof payload === 'object' && payload !== null
        ? payload.message ?? payload.detail ?? payload.title ?? response.statusText
        : payload || response.statusText

    const code = typeof payload === 'object' && payload !== null ? payload.code : undefined
    const error = new ApiError(message, { code, status: response.status })
    if (response.status === 401) {
      unauthorizedHandler?.(error)
    }
    throw error
  }

  return payload
}

const request = async (path, { body, query, ...options } = {}) => {
  const response = await fetch(buildUrl(path, query), {
    headers: {
      Accept: 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options.headers,
    },
    body: body ? JSON.stringify(body) : undefined,
    ...options,
  })

  return parseResponse(response)
}

export const apiClient = {
  get(path, options) {
    return request(path, { ...options, method: 'GET' })
  },
  post(path, body, options) {
    return request(path, { ...options, method: 'POST', body })
  },
  put(path, body, options) {
    return request(path, { ...options, method: 'PUT', body })
  },
}
