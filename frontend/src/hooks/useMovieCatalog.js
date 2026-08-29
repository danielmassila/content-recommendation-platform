import { useCallback, useDeferredValue, useEffect, useState } from 'react'
import { getLatestRatingsByItemId, toMovieCard } from '../mappers'
import { itemsApi, ratingsApi } from '../services'

export const useMovieCatalog = ({
  genre = 'all',
  minVote = '',
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
  const deferredQuery = useDeferredValue(query.trim())
  const [catalogPage, setCatalogPage] = useState({
    totalItems: 0,
    totalPages: 1,
  })

  const loadCatalog = useCallback(async ({ shouldUpdate = () => true } = {}) => {
    if (!enabled) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const [catalog, ratings] = await Promise.all([
        itemsApi.getItems({
          genre: genre === 'all' ? '' : genre,
          minVote,
          page: page - 1,
          query: deferredQuery,
          ratingStatus,
          size: pageSize,
          year,
        }),
        userId ? ratingsApi.getCurrentUserRatings({ limit: 50 }) : Promise.resolve([]),
      ])
      const items = catalog.items ?? []
      const ratingsByItemId = getLatestRatingsByItemId(ratings)
      const mappedMovies = items.map((item, index) =>
        toMovieCard(item, null, index, ratingsByItemId.get(item.id)),
      )

      if (shouldUpdate()) {
        setMovies(mappedMovies)
        setCatalogPage({
          totalItems: catalog.totalItems ?? mappedMovies.length,
          totalPages: Math.max(catalog.totalPages ?? 1, 1),
        })
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
  }, [deferredQuery, enabled, genre, minVote, page, pageSize, ratingStatus, userId, year])

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

  const pageCount = catalogPage.totalPages
  const currentPage = Math.min(Math.max(page, 1), pageCount)

  return {
    catalogRows: [
      {
        id: 'catalog',
        title: 'Catalogue',
        items: movies,
      },
    ],
    currentPage,
    error,
    isEmpty: !isLoading && !error && movies.length === 0,
    isLoading,
    movies,
    pageCount,
    refresh,
    totalCount: catalogPage.totalItems,
    totalResults: movies.length,
  }
}
