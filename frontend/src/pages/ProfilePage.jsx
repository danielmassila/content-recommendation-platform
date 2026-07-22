import { EmptyState, ErrorState, LoadingState } from '../components/ui'
import { useAuth, useUserProfile } from '../hooks'

const ProfilePage = () => {
  const { user: currentUser } = useAuth()
  const { error, initials, isEmpty, isLoading, ratedMovieRows, refresh, stats, user } =
    useUserProfile(currentUser?.id)

  return (
    <section className="page page--profile">
      <aside className="profile-card">
        <span className="profile-avatar">{initials}</span>
        <h1>{user?.username ?? currentUser?.name ?? 'Utilisateur'}</h1>
        <p>{user?.email ?? `Compte #${currentUser?.id}`}</p>
        <section className="profile-algo-card">
          <h2>Algo utilisé</h2>
          <strong>hybrid_usercf_pop</strong>
          <p>
            Mélange entre popularité pondérée et similarité entre utilisateurs. Les prochaines notes rendront le profil
            plus précis.
          </p>
        </section>
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

        {isEmpty ? <EmptyState title="Aucune note récente pour ce compte" /> : null}

        {!isLoading && !error ? (
          <section className="rating-history" aria-labelledby="rating-history-title">
            <h2 id="rating-history-title">Notes récentes</h2>
            <div className="rating-history__list">
              {ratedMovieRows[0]?.items.map((movie) => {
                const rating = Number(movie.rating?.rating ?? 0)
                return (
                  <article className="rating-history__item" key={movie.id}>
                    <div>
                      <h3>{movie.title}</h3>
                      <p>{movie.year} · {movie.genres.join(' / ')}</p>
                    </div>
                    <div className="rating-meter" aria-label={`Note ${rating} sur 5`}>
                      <span style={{ width: `${(rating / 5) * 100}%` }} />
                    </div>
                    <strong>{rating}/5</strong>
                  </article>
                )
              })}
            </div>
          </section>
        ) : null}
      </div>
    </section>
  )
}

export default ProfilePage
