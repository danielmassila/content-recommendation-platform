import { useCallback, useEffect, useState } from 'react'
import { itemsApi, recommendationsApi } from '../services'

const posterTones = ['mint', 'blue', 'peach', 'amber', 'violet', 'slate', 'sand', 'steel', 'green']

const parseMetadata = (metadata) => {
  if (!metadata) {
    return {}
  }

  if (typeof metadata !== 'string') {
    return metadata
  }

  try {
    return JSON.parse(metadata)
  } catch {
    return {}
  }
}

const normalizeGenres = (metadata, itemType) => {
  if (Array.isArray(metadata.genres)) {
    return metadata.genres
  }

  if (typeof metadata.genres === 'string') {
    return metadata.genres.split(',').map((genre) => genre.trim())
  }

  return [itemType ?? 'Film']
}

const toMatchPercent = (score) => {
  if (typeof score !== 'number') {
    return 0
  }

  return Math.round(score <= 1 ? score * 100 : score)
}

const toMovieCard = (recommendation, item, index) => {
  const metadata = parseMetadata(item.metadata)

  return {
    id: item.id,
    title: item.title,
    year: metadata.year ?? metadata.releaseYear ?? 'Année inconnue',
    duration: metadata.duration ?? 'Durée inconnue',
    genres: normalizeGenres(metadata, item.type),
    match: toMatchPercent(recommendation.score),
    description:
      recommendation.reason ??
      'Une recommandation calculée à partir de tes notes et des similarités avec les autres profils.',
    posterTone: posterTones[index % posterTones.length],
    recommendation,
  }
}

export const useRecommendations = (
  userId,
  { limit = 20, includeReason = true, algo, enabled = Boolean(userId) } = {},
) => {
  const [movies, setMovies] = useState([])
  const [isLoading, setIsLoading] = useState(enabled)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const loadRecommendations = useCallback(async ({ shouldUpdate = () => true } = {}) => {
    if (!enabled) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const recommendations = await recommendationsApi.getUserRecommendations(userId, {
        limit,
        includeReason,
        algo,
      })

      const moviesWithItems = await Promise.all(
        [...recommendations]
          .sort((a, b) => a.rank - b.rank)
          .map(async (recommendation, index) => {
            const item = await itemsApi.getItemById(recommendation.itemId)
            return toMovieCard(recommendation, item, index)
          }),
      )

      if (shouldUpdate()) {
        setMovies(moviesWithItems)
      }
    } catch (caughtError) {
      if (shouldUpdate()) {
        setError(caughtError)
        setMovies([])
      }
    } finally {
      if (shouldUpdate()) {
        setIsLoading(false)
      }
    }
  }, [algo, enabled, includeReason, limit, userId])

  const refresh = useCallback(() => {
    setReloadKey((currentKey) => currentKey + 1)
  }, [])

  useEffect(() => {
    let isCurrentRequest = true

    // Data fetching is the external synchronization point for this hook.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadRecommendations({ shouldUpdate: () => isCurrentRequest })

    return () => {
      isCurrentRequest = false
    }
  }, [loadRecommendations, reloadKey])

  return {
    error,
    featuredPick: movies[0] ?? null,
    isEmpty: !isLoading && !error && movies.length === 0,
    isLoading,
    movies,
    recommendationRows: [
      {
        id: 'recommended',
        title: 'Recommandé pour toi',
        items: movies,
      },
    ],
    refresh,
  }
}
