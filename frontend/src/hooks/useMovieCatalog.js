import { useCallback, useEffect, useMemo, useState } from 'react'
import { getLatestRatingsByItemId, toMovieCard } from '../mappers'
import { itemsApi, ratingsApi } from '../services'

const normalizeSearch = (value) => {
  return value.trim().toLowerCase()
}

export const useMovieCatalog = ({
  genre = 'all',
  minVote = '',
  limit = 100,
  page = 1,
  pageSize = 12,
  query = '',
  ratingStatus = 'all',
  userId,
  year = '',
  enabled = true,
} = {}) => {
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
    const searchQuery = normalizeSearch(query)

    return movies.filter((movie) => {
      const matchesGenre =
        genre === 'all' ||
        movie.genres.some((movieGenre) => movieGenre.toLowerCase() === genre.toLowerCase())
      const matchesYear = !year || String(movie.year) === String(year)
      const matchesVote = !minVote || Number(movie.voteAverage ?? 0) >= Number(minVote)
      const matchesRatingStatus =
        ratingStatus === 'all' ||
        (ratingStatus === 'rated' && movie.rating) ||
        (ratingStatus === 'unrated' && !movie.rating)
      const matchesSearch =
        !searchQuery ||
        movie.title.toLowerCase().includes(searchQuery) ||
        movie.originalTitle?.toLowerCase().includes(searchQuery) ||
        movie.directors.some((director) => director.toLowerCase().includes(searchQuery))

      return matchesGenre && matchesYear && matchesVote && matchesRatingStatus && matchesSearch
    })
  }, [genre, minVote, movies, query, ratingStatus, year])

  const pageCount = Math.max(1, Math.ceil(filteredMovies.length / pageSize))
  const currentPage = Math.min(Math.max(page, 1), pageCount)
  const paginatedMovies = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return filteredMovies.slice(startIndex, startIndex + pageSize)
  }, [currentPage, filteredMovies, pageSize])

  return {
    catalogRows: [
      {
        id: 'catalog',
        title: 'Catalogue',
        items: paginatedMovies,
      },
    ],
    currentPage,
    error,
    isEmpty: !isLoading && !error && filteredMovies.length === 0,
    isLoading,
    movies: filteredMovies,
    pageCount,
    refresh,
    totalCount: movies.length,
    totalResults: filteredMovies.length,
    years: [...new Set(movies.map((movie) => movie.year).filter((movieYear) => Number(movieYear)))].sort(
      (a, b) => Number(b) - Number(a),
    ),
  }
}
