import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from './apiClient'
import { itemsApi } from './itemsApi'

describe('itemsApi', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('requests a server-side catalog page', async () => {
    const get = vi.spyOn(apiClient, 'get').mockResolvedValue({ items: [] })

    await itemsApi.getItems({ page: 2, query: 'dune', size: 12 })

    expect(get).toHaveBeenCalledWith('/api/v1/items', {
      query: { page: 2, query: 'dune', size: 12, type: 'MOVIE' },
    })
  })
})
