import { useCallback, useEffect, useState } from 'react'
import { preferenceTypes } from '../data/preferences'

const STORAGE_KEY = 'content-reco-preferences'

const defaultPreferences = {
  entries: [],
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
  const [activeType, setActiveType] = useState(preferenceTypes[0].id)

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences))
  }, [preferences])

  const addPreference = useCallback(({ type, value }) => {
    const cleanedValue = value.trim()
    if (!cleanedValue) {
      return
    }

    setPreferences((currentPreferences) => ({
      ...currentPreferences,
      entries: [
        ...currentPreferences.entries.filter(
          (entry) =>
            entry.type !== type || entry.value.toLowerCase() !== cleanedValue.toLowerCase(),
        ),
        { id: `${type}-${cleanedValue.toLowerCase()}`, type, value: cleanedValue },
      ],
    }))
  }, [])

  const removePreference = useCallback((preferenceId) => {
    setPreferences((currentPreferences) => ({
      ...currentPreferences,
      entries: currentPreferences.entries.filter((entry) => entry.id !== preferenceId),
    }))
  }, [])

  const getEntriesByType = useCallback((type) => {
    return preferences.entries.filter((entry) => entry.type === type)
  }, [preferences.entries])

  return {
    activeType,
    addPreference,
    getEntriesByType,
    preferences,
    removePreference,
    setActiveType,
  }
}
