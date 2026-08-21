import { describe, expect, it } from 'vitest'
import { getLatestGeneratedAt, mapRecommendationItems } from './useRecommendations'

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

  it('maps embedded items without an additional API lookup', () => {
    const movies = mapRecommendationItems(
      [
        {
          itemId: 10,
          rank: 1,
          score: 0.9,
          item: { id: 10, title: 'Dune', type: 'MOVIE', metadata: '{"year":2021}' },
        },
      ],
      new Map(),
    )

    expect(movies).toHaveLength(1)
    expect(movies[0]).toMatchObject({ id: 10, title: 'Dune', year: 2021, match: 90 })
  })
})
