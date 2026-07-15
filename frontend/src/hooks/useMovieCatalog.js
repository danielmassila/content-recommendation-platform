import { useCallback, useEffect, useState } from 'react'
import { toMovieCard } from '../mappers'
import { itemsApi } from '../services'

export const useMovieCatalog = ({ limit = 50, enabled = true } = {}) => {
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
      const items = await itemsApi.getItems({ limit })
      const mappedMovies = items.map((item, index) => toMovieCard(item, null, index))

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
  }, [enabled, limit])

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

  return {
    catalogRows: [
      {
        id: 'catalog',
        title: 'Catalogue',
        items: movies,
      },
    ],
    error,
    isEmpty: !isLoading && !error && movies.length === 0,
    isLoading,
    movies,
    refresh,
  }
}
