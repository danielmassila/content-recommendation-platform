import { describe, expect, it } from 'vitest'
import { getLatestGeneratedAt } from './useRecommendations'

describe('recommendation freshness', () => {
  it('keeps ISO dates sortable for the latest generated recommendation', () => {
    const movies = [
      { recommendation: { generatedAt: '2026-08-20T10:00:00Z' } },
      { recommendation: { generatedAt: '2026-08-21T09:30:00Z' } },
      { recommendation: { generatedAt: '2026-08-19T18:00:00Z' } },
    ]

    expect(getLatestGeneratedAt(movies)).toBe('2026-08-21T09:30:00.000Z')
  })

  it('ignores invalid or absent generation dates', () => {
    expect(getLatestGeneratedAt([{ recommendation: { generatedAt: 'invalid' } }, {}])).toBeNull()
  })
})
