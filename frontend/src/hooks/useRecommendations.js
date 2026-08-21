import { useCallback, useEffect, useMemo, useState } from 'react'
import { getLatestRatingsByItemId, toMovieCard } from '../mappers'
import { itemsApi, ratingsApi, recommendationsApi } from '../services'

export const getLatestGeneratedAt = (movies) => {
  const timestamps = movies
    .map((movie) => movie.recommendation?.generatedAt)
    .filter(Boolean)
    .map((value) => new Date(value).getTime())
    .filter(Number.isFinite)

  return timestamps.length ? new Date(Math.max(...timestamps)).toISOString() : null
}

export const useRecommendations = (
  userId,
  { limit = 20, includeReason = true, algo, enabled = Boolean(userId) } = {},
) => {
  const [movies, setMovies] = useState([])
  const [isLoading, setIsLoading] = useState(enabled)
  const [isRecomputing, setIsRecomputing] = useState(false)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const mapRecommendations = useCallback(async (recommendations, ratingsByItemId) => {
    return Promise.all(
      [...recommendations]
        .sort((a, b) => a.rank - b.rank)
        .map(async (recommendation, index) => {
          const item = await itemsApi.getItemById(recommendation.itemId)
          return toMovieCard(item, recommendation, index, ratingsByItemId.get(item.id))
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
      const [recommendations, ratings] = await Promise.all([
        recommendationsApi.getCurrentUserRecommendations({
          limit,
          includeReason,
          algo,
        }),
        ratingsApi.getCurrentUserRatings({ limit: 50 }),
      ])
      const ratingsByItemId = getLatestRatingsByItemId(ratings)

      const moviesWithItems = await mapRecommendations(recommendations, ratingsByItemId)

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
  }, [algo, enabled, includeReason, limit, mapRecommendations])

  const recompute = useCallback(async () => {
    if (!enabled) {
      return
    }

    setIsRecomputing(true)
    setError(null)

    try {
      const [recommendations, ratings] = await Promise.all([
        recommendationsApi.recomputeCurrentUserRecommendations({
          limit,
          includeReason,
          algo,
        }),
        ratingsApi.getCurrentUserRatings({ limit: 50 }),
      ])
      const ratingsByItemId = getLatestRatingsByItemId(ratings)
      const moviesWithItems = await mapRecommendations(recommendations, ratingsByItemId)
      setMovies(moviesWithItems)
    } catch (caughtError) {
      setError(caughtError)
      setMovies([])
    } finally {
      setIsRecomputing(false)
    }
  }, [algo, enabled, includeReason, limit, mapRecommendations])

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

  const unratedMovies = useMemo(() => {
    return movies.filter((movie) => !movie.rating)
  }, [movies])

  const ratedMovies = useMemo(() => {
    return movies.filter((movie) => movie.rating)
  }, [movies])

  const lastGeneratedAt = useMemo(() => {
    return getLatestGeneratedAt(movies)
  }, [movies])

  return {
    error,
    featuredPick: unratedMovies[0] ?? null,
    isEmpty: !isLoading && !error && movies.length === 0,
    isLoading,
    isRecomputing,
    lastGeneratedAt,
    movies,
    ratedRecommendationRows: [
      {
        id: 'rated-recommendations',
        title: 'Déjà notés',
        items: ratedMovies,
      },
    ],
    recommendationRows: [
      {
        id: 'recommended',
        title: 'Recommandé pour toi',
        items: unratedMovies,
      },
    ],
    recompute,
    refresh,
  }
}
