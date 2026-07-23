import { useEffect } from 'react'

const formatVote = (movie) => {
  if (!movie.voteAverage) {
    return null
  }

  const vote = Number(movie.voteAverage).toFixed(1)
  return movie.voteCount ? `${vote}/10 · ${movie.voteCount} votes` : `${vote}/10`
}

const MovieDetailsModal = ({ isRatingSaving = false, movie, onClose, onRate, ratingError }) => {
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!movie) {
    return null
  }

  const vote = formatVote(movie)
  const currentRating = movie.rating?.rating
  const visualUrl = movie.posterUrl ?? movie.backdropUrl
  const hasVisual = Boolean(visualUrl)
  const dialogClassName = [
    'movie-modal__dialog',
    hasVisual ? '' : 'movie-modal__dialog--no-visual',
  ]
    .filter(Boolean)
    .join(' ')
  const visualClassName = [
    `movie-modal__visual movie-card--${movie.posterTone}`,
    movie.posterUrl ? 'movie-modal__visual--poster' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="movie-modal" role="presentation" onMouseDown={onClose}>
      <article
        aria-labelledby="movie-modal-title"
        aria-modal="true"
        className={dialogClassName}
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
      >
        <button
          aria-label="Fermer la fiche film"
          className="movie-modal__close"
          onClick={onClose}
          type="button"
        >
          ×
        </button>
        {hasVisual ? (
          <div className={visualClassName} aria-hidden="true">
            <img alt="" className="movie-modal__image" src={visualUrl} />
          </div>
        ) : null}
        <div className="movie-modal__content">
          <div className="movie-modal__header">
            <h2 id="movie-modal-title">{movie.title}</h2>
          </div>

          <div className="metadata">
            <span>{movie.year}</span>
            <span>{movie.duration}</span>
            {vote ? <span>{vote}</span> : null}
            {movie.genres.map((genre) => (
              <span key={genre}>{genre}</span>
            ))}
          </div>

          <p>{movie.description}</p>

          <section className="movie-modal__rating" aria-labelledby="movie-rating-title">
            <div>
              <h3 id="movie-rating-title">Ta note</h3>
              <p>
                {currentRating ? (
                  <>
                    Ta note actuelle : {currentRating}/5.
                    <br />
                    Tu peux la modifier.
                  </>
                ) : (
                  'Note ce film pour améliorer tes recommandations.'
                )}
              </p>
            </div>
            <div className="rating-picker" aria-label="Noter le film">
              {[1, 2, 3, 4, 5].map((grade) => (
                <button
                  aria-pressed={Number(currentRating) === grade}
                  className="rating-button"
                  disabled={isRatingSaving}
                  key={grade}
                  onClick={() => onRate?.(movie, grade)}
                  type="button"
                >
                  {grade}
                </button>
              ))}
            </div>
            {ratingError ? (
              <p className="form-error" role="alert">
                {ratingError.message}
              </p>
            ) : null}
          </section>

          <dl className="movie-modal__facts">
            {movie.directors?.length ? (
              <div>
                <dt>Réalisation</dt>
                <dd>{movie.directors.join(', ')}</dd>
              </div>
            ) : null}
            {movie.cast?.length ? (
              <div>
                <dt>Avec</dt>
                <dd>{movie.cast.slice(0, 5).join(', ')}</dd>
              </div>
            ) : null}
            {movie.originalTitle ? (
              <div>
                <dt>Titre original</dt>
                <dd>{movie.originalTitle}</dd>
              </div>
            ) : null}
            {movie.originalLanguage ? (
              <div>
                <dt>Langue originale</dt>
                <dd>{movie.originalLanguage.toUpperCase()}</dd>
              </div>
            ) : null}
          </dl>
        </div>
      </article>
    </div>
  )
}

export default MovieDetailsModal
