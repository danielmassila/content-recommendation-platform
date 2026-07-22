import { useCallback, useEffect, useMemo, useState } from 'react'
import { getLatestRatingsByItemId, toMovieCard } from '../mappers'
import { itemsApi, ratingsApi } from '../services'

export const useMovieCatalog = ({ genre = 'all', limit = 50, userId, enabled = true } = {}) => {
  const [movies, setMovies] = useState([])
  const [isLoading, setIsLoading] = useState(enabled)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const loadCatalog = useCallback(async ({ shouldUpdate = () => true } = {}) => {
    if (!enabled) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const [items, ratings] = await Promise.all([
        itemsApi.getItems({ limit }),
        userId ? ratingsApi.getUserRatings(userId, { limit: 500 }) : Promise.resolve([]),
      ])
      const ratingsByItemId = getLatestRatingsByItemId(ratings)
      const mappedMovies = items.map((item, index) =>
        toMovieCard(item, null, index, ratingsByItemId.get(item.id)),
      )

      if (shouldUpdate()) {
        setMovies(mappedMovies)
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
  }, [enabled, limit, userId])

  const refresh = useCallback(() => {
    setReloadKey((currentKey) => currentKey + 1)
  }, [])

  useEffect(() => {
    let isCurrentRequest = true

    // Data fetching is the external synchronization point for this hook.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadCatalog({ shouldUpdate: () => isCurrentRequest })

    return () => {
      isCurrentRequest = false
    }
  }, [loadCatalog, reloadKey])

  const filteredMovies = useMemo(() => {
    if (genre === 'all') {
      return movies
    }

    return movies.filter((movie) =>
      movie.genres.some((movieGenre) => movieGenre.toLowerCase() === genre.toLowerCase()),
    )
  }, [genre, movies])

  return {
    catalogRows: [
      {
        id: 'catalog',
        title: 'Catalogue',
        items: filteredMovies,
      },
    ],
    error,
    isEmpty: !isLoading && !error && filteredMovies.length === 0,
    isLoading,
    movies: filteredMovies,
    refresh,
  }
}
