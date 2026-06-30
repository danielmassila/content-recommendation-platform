import MovieRow from '../components/media/MovieRow'
import { movieRows, profileStats } from '../data/movies'

const ProfilePage = () => {
  return (
    <section className="page page--profile">
      <aside className="profile-card">
        <span className="profile-avatar">D</span>
        <h1>Daniel</h1>
        <p>daniel@username.fr</p>
      </aside>

      <div className="profile-content">
        <div className="stats-grid">
          {profileStats.map((stat) => (
            <article className="stat-card" key={stat.label}>
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </article>
          ))}
        </div>
        {/* TODO profile: remplacer par l'historique réel des notes utilisateur. */}
        <MovieRow row={movieRows[1]} />
        <section className="recommendation-note">
          <h2>Algo de recommandation</h2>
          <p>
            Bientôt, cette zone expliquera pourquoi un film est proposé : genres, notes passées, durée et humeur du soir.
          </p>
        </section>
      </div>
    </section>
  )
}

export default ProfilePage
