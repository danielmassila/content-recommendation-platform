import { useNavigate } from 'react-router-dom'
import Button from '../components/ui/Button'
import { useAuth } from '../hooks'

const HomePage = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  return (
    <section className="page page--home">
      <div className="home-hero">
        <p className="eyebrow">Ce soir, sans hésiter</p>
        <h1>Qu&apos;est-ce qu&apos;on regarde ce soir ?</h1>
        <p className="hero-copy">
          Démarre avec quelques préférences, puis explore un catalogue enrichi pour construire des recommandations
          qui deviennent vraiment les tiennes.
        </p>
        <div className="hero-actions">
          <Button onClick={() => navigate(isAuthenticated ? '/preferences' : '/login')}>
            {isAuthenticated ? 'Démarrer mes préférences' : 'Créer mon espace'}
          </Button>
          <Button variant="secondary" onClick={() => navigate('/discover')}>
            Explorer le catalogue
          </Button>
        </div>
      </div>
    </section>
  )
}

export default HomePage
