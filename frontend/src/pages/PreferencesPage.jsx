import { preferenceOptions } from '../data/movies'
import Button from '../components/ui/Button'

const PreferencesPage = ({ onNavigate }) => {
  return (
    <section className="page page--preferences">
      <div className="preference-panel">
        <p className="eyebrow">Démarrage</p>
        <h1>Quel est ton genre préféré ?</h1>
        <div className="preference-grid">
          {preferenceOptions.map((option) => (
            <button className="preference-option" key={option.id} type="button">
              <span>{option.label}</span>
              <small>{option.hint}</small>
            </button>
          ))}
        </div>
        {/* TODO preferences: persister les réponses et enrichir la question suivante depuis le backend. */}
        <Button onClick={() => onNavigate('discovery')}>Je préfère...</Button>
      </div>
    </section>
  )
}

export default PreferencesPage
