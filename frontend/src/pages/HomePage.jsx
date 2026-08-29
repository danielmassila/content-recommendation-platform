import { useNavigate } from 'react-router-dom'
import Button from '../components/ui/Button'
import { useAuth } from '../hooks'

const HomePage = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  return (
    <section className="page page--home">
      <div className="home-hero">
        <div className="terminal-frame">
          <div className="terminal-screen">
            <div className="terminal-screen__content">
              <p className="eyebrow">Recommandations personnalisées</p>
              <h1>Trouvez un film qui vous ressemble.</h1>
              <p className="hero-copy">
                Indiquez ce que vous aimez et découvrez une sélection construite à partir de vos préférences.
              </p>
              <div className="hero-actions">
                <Button onClick={() => navigate(isAuthenticated ? '/preferences' : '/login')}>
                  {isAuthenticated ? 'Modifier mes préférences' : 'Créer mon profil'}
                </Button>
                <Button variant="secondary" onClick={() => navigate('/discover')}>
                  Découvrir les films
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default HomePage
