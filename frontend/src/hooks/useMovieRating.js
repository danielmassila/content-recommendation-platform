import { useCallback, useState } from 'react'
import { ratingsApi } from '../services'

export const useMovieRating = (userId) => {
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState(null)
  const [lastRating, setLastRating] = useState(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const rateMovie = useCallback(async (movie, grade) => {
    if (!userId || !movie?.id) {
      return null
    }

    setIsSaving(true)
    setError(null)

    try {
      const rating = await ratingsApi.rateItem(movie.id, grade)
      setLastRating({ movieId: movie.id, rating })
      return rating
    } catch (caughtError) {
      setError(caughtError)
      throw caughtError
    } finally {
      setIsSaving(false)
    }
  }, [userId])

  return {
    clearError,
    error,
    isSaving,
    lastRating,
    rateMovie,
  }
}
