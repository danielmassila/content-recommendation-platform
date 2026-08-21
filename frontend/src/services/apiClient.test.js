import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiClient, setApiAccessToken, setUnauthorizedHandler } from './apiClient'

describe('apiClient', () => {
  afterEach(() => {
    setApiAccessToken(null)
    setUnauthorizedHandler(null)
    vi.unstubAllGlobals()
  })

  it('adds query parameters and parses JSON responses', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: 7 }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiClient.get('/api/v1/items', { query: { limit: 10 } })).resolves.toEqual({ id: 7 })
    expect(fetchMock.mock.calls[0][0].toString()).toContain('/api/v1/items?limit=10')
  })

  it('adds the bearer token and exposes the API error message', async () => {
    setApiAccessToken('secret-token')
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: 'Not found' }), {
      headers: { 'Content-Type': 'application/json' },
      status: 404,
    }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiClient.get('/api/v1/missing')).rejects.toThrow('Not found')
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer secret-token')
  })

  it('notifies the session manager when authentication expires', async () => {
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: 'AUTHENTICATION_REQUIRED',
      detail: 'Authentication is required',
    }), {
      headers: { 'Content-Type': 'application/problem+json' },
      status: 401,
    })))

    await expect(apiClient.get('/api/v1/me')).rejects.toMatchObject({
      code: 'AUTHENTICATION_REQUIRED',
      status: 401,
    })
    expect(onUnauthorized).toHaveBeenCalledOnce()
  })
})
