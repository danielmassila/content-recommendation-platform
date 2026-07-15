import { useNavigate } from 'react-router-dom'
import { preferenceOptions } from '../data/movies'
import { Button, RadioCard } from '../components/ui'
import { usePreferences } from '../hooks'

const PreferencesPage = () => {
  const navigate = useNavigate()
  const { preferences, updatePreference } = usePreferences()

  return (
    <section className="page page--preferences">
      <div className="preference-panel">
        <p className="eyebrow">Démarrage</p>
        <h1>Quel est ton genre préféré ?</h1>
        <div className="preference-grid">
          {preferenceOptions.map((option) => (
            <RadioCard
              checked={preferences.favoriteGenre === option.id}
              hint={option.hint}
              key={option.id}
              label={option.label}
              name="favoriteGenre"
              onChange={() => updatePreference('favoriteGenre', option.id)}
              value={option.id}
            />
          ))}
        </div>
        <Button onClick={() => navigate('/discover')}>Je préfère...</Button>
      </div>
    </section>
  )
}

export default PreferencesPage
