import { useEffect } from 'react'

const formatVote = (movie) => {
  if (!movie.voteAverage) {
    return null
  }

  const vote = Number(movie.voteAverage).toFixed(1)
  return movie.voteCount ? `${vote}/10 · ${movie.voteCount} votes` : `${vote}/10`
}

const MovieDetailsModal = ({ movie, onClose }) => {
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
  const visualStyle =
    movie.backdropUrl || movie.posterUrl
      ? { backgroundImage: `url(${movie.backdropUrl ?? movie.posterUrl})` }
      : undefined

  return (
    <div className="movie-modal" role="presentation" onMouseDown={onClose}>
      <article
        aria-labelledby="movie-modal-title"
        aria-modal="true"
        className="movie-modal__dialog"
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
        <div
          className={`movie-modal__visual movie-card--${movie.posterTone}`}
          style={visualStyle}
          aria-hidden="true"
        />
        <div className="movie-modal__content">
          <div className="movie-modal__header">
            <div>
              <p className="eyebrow">Fiche film</p>
              <h2 id="movie-modal-title">{movie.title}</h2>
            </div>
          </div>

          <div className="metadata">
            <span>{movie.year}</span>
            <span>{movie.duration}</span>
            {vote ? <span>{vote}</span> : null}
          </div>

          <p>{movie.description}</p>

          <dl className="movie-modal__facts">
            <div>
              <dt>Genres</dt>
              <dd>{movie.genres.join(' / ')}</dd>
            </div>
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
