import MovieRow from '../components/media/MovieRow'
import { EmptyState, ErrorState, LoadingState } from '../components/ui'
import { useUserProfile } from '../hooks'

const demoUserId = 1

const ProfilePage = () => {
  const { error, initials, isEmpty, isLoading, ratedMovieRows, refresh, stats, user } =
    useUserProfile(demoUserId)

  return (
    <section className="page page--profile">
      <aside className="profile-card">
        <span className="profile-avatar">{initials}</span>
        <h1>{user?.email ?? 'Utilisateur'}</h1>
        <p>Utilisateur de démo #{demoUserId}</p>
      </aside>

      <div className="profile-content">
        {isLoading ? <LoadingState title="Chargement du profil..." /> : null}

        {error ? (
          <ErrorState
            error={error}
            eyebrow="Profil indisponible"
            onRetry={refresh}
            title="Impossible de charger le profil"
          />
        ) : null}

        <div className="stats-grid">
          {stats.map((stat) => (
            <article className="stat-card" key={stat.label}>
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </article>
          ))}
        </div>

        {isEmpty ? <EmptyState title="Aucune note récente pour cet utilisateur" /> : null}

        {!isLoading && !error
          ? ratedMovieRows.map((row) => <MovieRow key={row.id} row={row} />)
          : null}

        <section className="recommendation-note">
          <h2>Algo de recommandation</h2>
          <p>
            Cette zone pourra afficher plus tard les signaux utilisés par l'algorithme :
            notes passées, similarités et contenus ignorés.
          </p>
        </section>
      </div>
    </section>
  )
}

export default ProfilePage
