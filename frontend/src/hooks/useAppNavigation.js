import { useCallback, useState } from 'react'

export const useAppNavigation = (initialPage = 'home') => {
  const [currentPage, setCurrentPage] = useState(initialPage)

  const goTo = useCallback((pageId) => {
    setCurrentPage(pageId)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  return { currentPage, goTo }
}
