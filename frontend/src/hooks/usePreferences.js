import { useCallback, useEffect, useState } from 'react'

const STORAGE_KEY = 'tonights-pick-preferences'

const defaultPreferences = {
  favoriteGenre: 'drama',
}

const readStoredPreferences = () => {
  try {
    const storedValue = window.localStorage.getItem(STORAGE_KEY)
    return storedValue ? { ...defaultPreferences, ...JSON.parse(storedValue) } : defaultPreferences
  } catch {
    return defaultPreferences
  }
}

export const usePreferences = () => {
  const [preferences, setPreferences] = useState(readStoredPreferences)

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences))
  }, [preferences])

  const updatePreference = useCallback((key, value) => {
    setPreferences((currentPreferences) => ({
      ...currentPreferences,
      [key]: value,
    }))
  }, [])

  return {
    preferences,
    updatePreference,
  }
}
