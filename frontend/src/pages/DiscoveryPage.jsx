import MovieCard from '../components/media/MovieCard'
import MovieRow from '../components/media/MovieRow'
import { Button, EmptyState, ErrorState, LoadingState } from '../components/ui'
import { useRecommendations } from '../hooks'

const demoUserId = 1

const DiscoveryPage = () => {
  const { error, featuredPick, isEmpty, isLoading, recommendationRows, refresh } =
    useRecommendations(demoUserId)

  return (
    <section className="page page--discovery">
      <div className="discovery-heading">
        <div>
          <p className="eyebrow">Sélection du moment</p>
          <h1>Trouvons ta prochaine pépite</h1>
        </div>
        <label className="select-field">
          Genre
          <select defaultValue="all">
            <option value="all">Tous les genres</option>
            <option value="drama">Drame</option>
            <option value="thriller">Thriller</option>
          </select>
        </label>
      </div>

      {isLoading ? (
        <LoadingState title="On cherche tes recommandations..." />
      ) : null}

      {error ? (
        <ErrorState
          error={error}
          eyebrow="API indisponible"
          onRetry={refresh}
          title="Impossible de charger les recommandations"
        />
      ) : null}

      {isEmpty ? (
        <EmptyState title="Pas encore de recommandation pour cet utilisateur" />
      ) : null}

      {featuredPick ? (
        <>
          <section className="featured-pick">
            <div className="featured-pick__copy">
              <p className="eyebrow">Sélection du moment</p>
              <h2>{featuredPick.title}</h2>
              <p>{featuredPick.description}</p>
              <div className="metadata">
                <span>{featuredPick.year}</span>
                <span>{featuredPick.duration}</span>
                <span>{featuredPick.genres.join(' / ')}</span>
              </div>
              <div className="featured-pick__actions">
                <Button>Détails</Button>
                <Button variant="secondary">Noter</Button>
              </div>
            </div>
            <MovieCard movie={featuredPick} compact />
          </section>

          <div className="api-note">
            Données chargées depuis l'API pour l'utilisateur de démo #{demoUserId}.
          </div>

          {recommendationRows.map((row) => (
            <MovieRow key={row.id} row={row} />
          ))}
        </>
      ) : null}
    </section>
  )
}

export default DiscoveryPage
