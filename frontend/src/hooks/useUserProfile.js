import { useCallback, useEffect, useMemo, useState } from 'react'
import { getLatestRatingsByItemId, toMovieCard } from '../mappers'
import { itemsApi, ratingsApi, usersApi } from '../services'

const getInitials = (email) => {
  return email?.trim().slice(0, 1).toUpperCase() || '?'
}

const formatRating = (rating) => {
  if (rating === undefined || rating === null) {
    return '-'
  }

  return Number(rating).toFixed(1).replace('.0', '')
}

export const useUserProfile = (userId, { ratingsLimit = 10, enabled = Boolean(userId) } = {}) => {
  const [user, setUser] = useState(null)
  const [ratedMovies, setRatedMovies] = useState([])
  const [isLoading, setIsLoading] = useState(enabled)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const loadProfile = useCallback(async ({ shouldUpdate = () => true } = {}) => {
    if (!enabled) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const [loadedUser, ratings] = await Promise.all([
        usersApi.getCurrentUser(),
        ratingsApi.getCurrentUserRatings({ limit: ratingsLimit }),
      ])
      const uniqueRatings = [...getLatestRatingsByItemId(ratings).values()]

      const movies = await Promise.all(
        uniqueRatings.map(async (rating, index) => {
          const item = await itemsApi.getItemById(rating.itemId)
          return toMovieCard(item, null, index, rating)
        }),
      )

      if (shouldUpdate()) {
        setUser(loadedUser)
        setRatedMovies(movies)
      }
    } catch (caughtError) {
      if (shouldUpdate()) {
        setError(caughtError)
        setUser(null)
        setRatedMovies([])
      }
    } finally {
      if (shouldUpdate()) {
        setIsLoading(false)
      }
    }
  }, [enabled, ratingsLimit])

  const refresh = useCallback(() => {
    setReloadKey((currentKey) => currentKey + 1)
  }, [])

  useEffect(() => {
    let isCurrentRequest = true

    // Data fetching is the external synchronization point for this hook.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadProfile({ shouldUpdate: () => isCurrentRequest })

    return () => {
      isCurrentRequest = false
    }
  }, [loadProfile, reloadKey])

  const stats = useMemo(() => {
    const lastRating = ratedMovies[0]?.rating?.rating
    const ratingValues = ratedMovies
      .map((movie) => movie.rating?.rating)
      .filter((rating) => rating !== undefined && rating !== null)
    const averageRating =
      ratingValues.length > 0
        ? ratingValues.reduce((total, rating) => total + Number(rating), 0) / ratingValues.length
        : null

    return [
      { label: 'Films notés', value: ratedMovies.length.toString() },
      { label: 'Note moyenne', value: formatRating(averageRating) },
      { label: 'Dernière note', value: formatRating(lastRating) },
    ]
  }, [ratedMovies])

  return {
    error,
    initials: getInitials(user?.email),
    isEmpty: !isLoading && !error && ratedMovies.length === 0,
    isLoading,
    ratedMovieRows: [
      {
        id: 'recent-ratings',
        title: 'Notes récentes',
        items: ratedMovies,
      },
    ],
    ratedMovies,
    refresh,
    stats,
    user,
  }
}
