import { useCallback, useEffect, useState } from 'react'
import { toMovieCard } from '../mappers'
import { itemsApi, recommendationsApi } from '../services'

export const useRecommendations = (
  userId,
  { limit = 20, includeReason = true, algo, enabled = Boolean(userId) } = {},
) => {
  const [movies, setMovies] = useState([])
  const [isLoading, setIsLoading] = useState(enabled)
  const [isRecomputing, setIsRecomputing] = useState(false)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const mapRecommendations = useCallback(async (recommendations) => {
    return Promise.all(
      [...recommendations]
        .sort((a, b) => a.rank - b.rank)
        .map(async (recommendation, index) => {
          const item = await itemsApi.getItemById(recommendation.itemId)
          return toMovieCard(item, recommendation, index)
        }),
    )
  }, [])

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

      const moviesWithItems = await mapRecommendations(recommendations)

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
  }, [algo, enabled, includeReason, limit, mapRecommendations, userId])

  const recompute = useCallback(async () => {
    if (!enabled) {
      return
    }

    setIsRecomputing(true)
    setError(null)

    try {
      const recommendations = await recommendationsApi.recomputeUserRecommendations(userId, {
        limit,
        includeReason,
        algo,
      })
      const moviesWithItems = await mapRecommendations(recommendations)
      setMovies(moviesWithItems)
    } catch (caughtError) {
      setError(caughtError)
      setMovies([])
    } finally {
      setIsRecomputing(false)
    }
  }, [algo, enabled, includeReason, limit, mapRecommendations, userId])

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
    isRecomputing,
    movies,
    recommendationRows: [
      {
        id: 'recommended',
        title: 'Recommandé pour toi',
        items: movies,
      },
    ],
    recompute,
    refresh,
  }
}
