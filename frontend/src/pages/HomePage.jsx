import Button from '../components/ui/Button'

const HomePage = ({ onNavigate }) => {
  return (
    <section className="page page--home">
      <div className="home-hero">
        <p className="eyebrow">Ce soir, sans hésiter</p>
        <h1>Qu&apos;est-ce qu&apos;on regarde ce soir ?</h1>
        <p className="hero-copy">
          Une recommandation sobre, rapide et personnelle pour arrêter de scroller avant même de lancer le film.
        </p>
        <div className="hero-actions">
          <Button onClick={() => onNavigate('preferences')}>Découvrir</Button>
          <Button variant="secondary" onClick={() => onNavigate('discovery')}>
            Voir le catalogue
          </Button>
        </div>
      </div>
    </section>
  )
}

export default HomePage
