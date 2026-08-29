import { useCallback, useEffect, useRef, useState } from 'react'
import { preferenceTypes } from '../data/preferences'
import { preferencesApi } from '../services'

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
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState(null)
  const [lastSavedAt, setLastSavedAt] = useState(null)
  const saveQueue = useRef(Promise.resolve())
  const saveSequence = useRef(0)

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences))
  }, [preferences])

  const loadPreferences = useCallback(async (userId, { shouldUpdate = () => true } = {}) => {
    if (!userId) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const loadedPreferences = await preferencesApi.getCurrentUserPreferences()
      if (shouldUpdate()) {
        setPreferences({
          entries: loadedPreferences.map((preference) => ({
            id: `${preference.type}-${preference.value.toLowerCase()}`,
            type: preference.type,
            value: preference.value,
          })),
        })
      }
    } catch (caughtError) {
      if (shouldUpdate()) {
        setError(caughtError)
      }
    } finally {
      if (shouldUpdate()) {
        setIsLoading(false)
      }
    }
  }, [])

  const savePreferences = useCallback(async (userId, nextPreferences) => {
    if (!userId) {
      return
    }

    const sequence = ++saveSequence.current
    setIsSaving(true)
    setError(null)

    saveQueue.current = saveQueue.current
      .catch(() => undefined)
      .then(() => preferencesApi.replaceCurrentUserPreferences(nextPreferences.entries))

    try {
      await saveQueue.current
      if (sequence === saveSequence.current) {
        setLastSavedAt(new Date())
      }
    } catch (caughtError) {
      if (sequence === saveSequence.current) {
        setError(caughtError)
      }
    } finally {
      if (sequence === saveSequence.current) {
        setIsSaving(false)
      }
    }
  }, [])

  const addPreference = useCallback(({ type, value, userId }) => {
    const cleanedValue = value.trim()
    if (!cleanedValue) {
      return
    }

    const nextPreferences = {
      ...preferences,
      entries: [
        ...preferences.entries.filter(
          (entry) =>
            entry.type !== type || entry.value.toLowerCase() !== cleanedValue.toLowerCase(),
        ),
        { id: `${type}-${cleanedValue.toLowerCase()}`, type, value: cleanedValue },
      ],
    }

    setPreferences(nextPreferences)
    savePreferences(userId, nextPreferences)
  }, [preferences, savePreferences])

  const removePreference = useCallback((preferenceId, userId) => {
    const nextPreferences = {
      ...preferences,
      entries: preferences.entries.filter((entry) => entry.id !== preferenceId),
    }

    setPreferences(nextPreferences)
    savePreferences(userId, nextPreferences)
  }, [preferences, savePreferences])

  const getEntriesByType = useCallback((type) => {
    return preferences.entries.filter((entry) => entry.type === type)
  }, [preferences.entries])

  return {
    activeType,
    addPreference,
    error,
    getEntriesByType,
    isLoading,
    isSaving,
    lastSavedAt,
    loadPreferences,
    preferences,
    removePreference,
    setActiveType,
  }
}
