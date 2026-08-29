import { useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { Button, EmptyState, LoadingState, TextField } from '../components/ui'
import { getPreferenceType, preferenceTypes } from '../data/preferences'
import { useAuth, usePreferences } from '../hooks'

const PreferencesPage = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const {
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
  } = usePreferences()
  const [inputValue, setInputValue] = useState('')
  const selectedType = getPreferenceType(activeType)
  const selectedEntries = getEntriesByType(activeType)
  const hasPreferences = preferences.entries.length > 0

  useEffect(() => {
    let isCurrentRequest = true

    loadPreferences(user?.id, { shouldUpdate: () => isCurrentRequest })

    return () => {
      isCurrentRequest = false
    }
  }, [loadPreferences, user?.id])

  const visibleSuggestions = useMemo(() => {
    const query = inputValue.trim().toLowerCase()
    const selectedValues = new Set(
      selectedEntries.map((entry) => entry.value.toLowerCase()),
    )

    return selectedType.suggestions.filter((suggestion) => {
      const isAlreadySelected = selectedValues.has(suggestion.toLowerCase())
      const matchesQuery = !query || suggestion.toLowerCase().includes(query)
      return !isAlreadySelected && matchesQuery
    })
  }, [inputValue, selectedEntries, selectedType.suggestions])

  const handleSubmit = (event) => {
    event.preventDefault()
    addPreference({ type: activeType, userId: user?.id, value: inputValue })
    setInputValue('')
  }

  const handleSuggestionClick = (suggestion) => {
    addPreference({ type: activeType, userId: user?.id, value: suggestion })
    setInputValue('')
  }

  return (
    <section className="page page--preferences">
      <div className="preference-panel">
        <p className="eyebrow">Démarrage</p>
        <h1>Dis-moi ce que tu aimes</h1>
        <p className="preference-panel__intro">
          Choisis un angle, ajoute quelques réponses, et on s’en servira comme point de départ pour personnaliser
          les recommandations.
        </p>

        {isLoading ? <LoadingState title="Chargement des préférences..." /> : null}

        {error ? (
          <div className="sync-warning" role="status">
            <p>Synchronisation indisponible. Les préférences locales restent utilisables.</p>
            <Button variant="secondary" onClick={() => loadPreferences(user?.id)}>
              Réessayer
            </Button>
          </div>
        ) : null}

        {lastSavedAt && !error ? (
          <p className="form-success" role="status">
            Préférences sauvegardées.
          </p>
        ) : null}

        <div className="preference-tabs" aria-label="Types de préférences">
          {preferenceTypes.map((type) => (
            <button
              aria-pressed={activeType === type.id}
              className="preference-tab"
              key={type.id}
              onClick={() => {
                setActiveType(type.id)
                setInputValue('')
              }}
              type="button"
            >
              {type.label}
            </button>
          ))}
        </div>

        <form className="preference-search" onSubmit={handleSubmit}>
          <TextField
            autoComplete="off"
            id="preference-value"
            label={selectedType.question}
            onChange={(event) => setInputValue(event.target.value)}
            placeholder={selectedType.placeholder}
            type="text"
            value={inputValue}
          />
          <Button disabled={!inputValue.trim()} type="submit">
            Ajouter
          </Button>
        </form>

        <div className="preference-suggestions" aria-label="Suggestions">
          {visibleSuggestions.map((suggestion) => (
            <button
              className="preference-suggestion"
              key={suggestion}
              onClick={() => handleSuggestionClick(suggestion)}
              type="button"
            >
              {suggestion}
            </button>
          ))}
        </div>

        <div className="preference-summary">
          {hasPreferences ? (
            preferences.entries.map((entry) => (
              <button
                className="preference-chip"
                key={entry.id}
                onClick={() => removePreference(entry.id, user?.id)}
                type="button"
              >
                <span>{getPreferenceType(entry.type).label}</span>
                {entry.value}
              </button>
            ))
          ) : (
            <EmptyState
              eyebrow="Profil vide"
              message="Ajoute au moins quelques goûts pour éviter des recommandations trop génériques."
              title="Aucune préférence ajoutée"
            />
          )}
        </div>

        <div className="preference-actions">
          <Button variant="secondary" onClick={() => navigate('/discover')}>
            Passer pour l’instant
          </Button>
          <Button disabled={!hasPreferences || isSaving} onClick={() => navigate('/discover')}>
            {isSaving ? 'Sauvegarde...' : 'Voir mes recommandations'}
          </Button>
        </div>
      </div>
    </section>
  )
}

export default PreferencesPage
