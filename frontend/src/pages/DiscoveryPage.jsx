import { useEffect, useState } from 'react'
import MovieCard from '../components/media/MovieCard'
import MovieDetailsModal from '../components/media/MovieDetailsModal'
import MovieRow from '../components/media/MovieRow'
import { Button, EmptyState, ErrorState, LoadingState, SelectField, TextField } from '../components/ui'
import { useAuth, useMovieCatalog, useMovieRating, useRecommendations } from '../hooks'

const DiscoveryPage = () => {
  const { user } = useAuth()
  const [catalogPage, setCatalogPage] = useState(1)
  const [catalogQuery, setCatalogQuery] = useState('')
  const [selectedGenre, setSelectedGenre] = useState('all')
  const [selectedMovie, setSelectedMovie] = useState(null)
  const {
    clearError: clearRatingError,
    error: ratingError,
    isSaving: isRatingSaving,
    rateMovie,
  } = useMovieRating(user?.id)
  const {
    error,
    featuredPick,
    isEmpty,
    isLoading,
    isRecomputing,
    ratedRecommendationRows,
    recommendationRows,
    recompute,
    refresh,
  } = useRecommendations(user?.id)
  const {
    catalogRows,
    currentPage,
    error: catalogError,
    isEmpty: isCatalogEmpty,
    isLoading: isCatalogLoading,
    pageCount,
    refresh: refreshCatalog,
    totalCount,
    totalResults,
  } = useMovieCatalog({
    genre: selectedGenre,
    limit: 100,
    page: catalogPage,
    pageSize: 12,
    query: catalogQuery,
    userId: user?.id,
  })

  useEffect(() => {
    clearRatingError()
  }, [clearRatingError, selectedMovie?.id])

  const hasRatedRecommendations = ratedRecommendationRows.some((row) => row.items.length > 0)
  const hasUnratedRecommendations = recommendationRows.some((row) => row.items.length > 0)

  const handleRateMovie = async (movie, grade) => {
    let rating = null
    try {
      rating = await rateMovie(movie, grade)
    } catch {
      return
    }

    if (!rating) {
      return
    }

    setSelectedMovie((currentMovie) =>
      currentMovie?.id === movie.id
        ? { ...currentMovie, rating }
        : currentMovie,
    )
    refresh()
    refreshCatalog()
  }

  return (
    <section className="page page--discovery">
      <div className="discovery-heading">
        <div>
          <p className="eyebrow">Sélection du moment</p>
          <h1>Trouvons ta prochaine pépite</h1>
        </div>
        <SelectField
          id="genre-filter"
          label="Genre"
          value={selectedGenre}
          onChange={(event) => {
            setSelectedGenre(event.target.value)
            setCatalogPage(1)
          }}
        >
          <option value="all">Tous les genres</option>
          <option value="Action">Action</option>
          <option value="Adventure">Aventure</option>
          <option value="Animation">Animation</option>
          <option value="Comedy">Comédie</option>
          <option value="Crime">Crime</option>
          <option value="Drama">Drame</option>
          <option value="Horror">Horreur</option>
          <option value="Romance">Romance</option>
          <option value="Sci-Fi">Science-fiction</option>
          <option value="Thriller">Thriller</option>
        </SelectField>
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
        <section className="recommendation-note recommendation-note--empty">
          <h2>Pas encore de recommandation pour ce compte</h2>
          <p>
            Génère une première sélection à partir de tes préférences et de la popularité, puis affine-la en notant
            quelques films.
          </p>
          <div className="recommendation-note__actions">
            <Button disabled={isRecomputing} onClick={recompute}>
              {isRecomputing ? 'Génération...' : 'Générer mes recommandations'}
            </Button>
          </div>
        </section>
      ) : null}

      {!isEmpty && !isLoading && !error && !hasUnratedRecommendations && hasRatedRecommendations ? (
        <section className="recommendation-note recommendation-note--empty">
          <h2>Toutes les recommandations actuelles sont déjà notées</h2>
          <p>
            Relance un calcul après avoir ajouté des préférences ou noté de nouveaux films pour faire remonter une
            nouvelle sélection.
          </p>
          <div className="recommendation-note__actions">
            <Button disabled={isRecomputing} onClick={recompute}>
              {isRecomputing ? 'Génération...' : 'Recalculer mes recommandations'}
            </Button>
          </div>
        </section>
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
                <Button onClick={() => setSelectedMovie(featuredPick)}>Détails</Button>
                <Button variant="secondary" onClick={() => setSelectedMovie(featuredPick)}>
                  Noter
                </Button>
              </div>
            </div>
            <MovieCard movie={featuredPick} compact onSelect={setSelectedMovie} />
          </section>

        </>
      ) : null}

      {!isLoading && !error
        ? recommendationRows
            .filter((row) => row.items.length > 0)
            .map((row) => (
              <MovieRow key={row.id} onMovieSelect={setSelectedMovie} row={row} />
            ))
        : null}

      {!isLoading && !error
        ? ratedRecommendationRows
            .filter((row) => row.items.length > 0)
            .map((row) => (
              <MovieRow key={row.id} onMovieSelect={setSelectedMovie} row={row} />
            ))
        : null}

      <section className="catalog-tools" aria-label="Filtres du catalogue">
        <TextField
          autoComplete="off"
          id="catalog-search"
          label="Recherche"
          onChange={(event) => {
            setCatalogQuery(event.target.value)
            setCatalogPage(1)
          }}
          placeholder="Titre ou réalisateur..."
          type="search"
          value={catalogQuery}
        />
        <p>
          {totalResults} résultat{totalResults > 1 ? 's' : ''} sur {totalCount}
        </p>
      </section>

      {isCatalogLoading ? (
        <LoadingState title="Chargement du catalogue..." />
      ) : null}

      {catalogError ? (
        <ErrorState
          error={catalogError}
          eyebrow="Catalogue indisponible"
          onRetry={refreshCatalog}
          title="Impossible de charger le catalogue"
        />
      ) : null}

      {isCatalogEmpty ? (
        <EmptyState
          message={
            catalogQuery
              ? 'Essaie un autre titre, réalisateur ou genre.'
              : 'Le catalogue ne contient aucun contenu pour ce filtre.'
          }
          title="Aucun film trouvé"
        />
      ) : null}

      {!isCatalogLoading && !catalogError
        ? catalogRows.map((row) => (
            <MovieRow key={row.id} onMovieSelect={setSelectedMovie} row={row} />
          ))
        : null}

      {!isCatalogLoading && !catalogError && !isCatalogEmpty ? (
        <nav className="catalog-pagination" aria-label="Pagination du catalogue">
          <Button
            disabled={currentPage <= 1}
            onClick={() => setCatalogPage((page) => Math.max(1, page - 1))}
            variant="secondary"
          >
            Précédent
          </Button>
          <span>
            Page {currentPage} / {pageCount}
          </span>
          <Button
            disabled={currentPage >= pageCount}
            onClick={() => setCatalogPage((page) => Math.min(pageCount, page + 1))}
            variant="secondary"
          >
            Suivant
          </Button>
        </nav>
      ) : null}

      <MovieDetailsModal
        isRatingSaving={isRatingSaving}
        movie={selectedMovie}
        onClose={() => setSelectedMovie(null)}
        onRate={handleRateMovie}
        ratingError={ratingError}
      />
    </section>
  )
}

export default DiscoveryPage
