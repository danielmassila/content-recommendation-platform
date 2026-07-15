import { useNavigate } from 'react-router-dom'
import { preferenceOptions } from '../data/movies'
import { Button, RadioCard } from '../components/ui'

const PreferencesPage = () => {
  const navigate = useNavigate()

  return (
    <section className="page page--preferences">
      <div className="preference-panel">
        <p className="eyebrow">Démarrage</p>
        <h1>Quel est ton genre préféré ?</h1>
        <div className="preference-grid">
          {preferenceOptions.map((option) => (
            <RadioCard
              hint={option.hint}
              key={option.id}
              label={option.label}
              name="favoriteGenre"
              value={option.id}
            />
          ))}
        </div>
        {/* TODO preferences: persister les réponses et enrichir la question suivante depuis le backend. */}
        <Button onClick={() => navigate('/discover')}>Je préfère...</Button>
      </div>
    </section>
  )
}

export default PreferencesPage
