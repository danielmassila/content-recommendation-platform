const MovieCard = ({ movie, compact = false, onSelect }) => {
  const badge = movie.rating ? `${movie.rating.rating}/5` : `${movie.match}% pertinent`
  const Component = onSelect ? 'button' : 'article'
  const directorLabel = movie.directors?.length ? movie.directors.slice(0, 2).join(', ') : null
  const voteLabel = movie.voteAverage ? `${Number(movie.voteAverage).toFixed(1)}/10` : null

  return (
    <Component
      className={`movie-card movie-card--${movie.posterTone} ${compact ? 'movie-card--compact' : ''}`.trim()}
      onClick={onSelect ? () => onSelect(movie) : undefined}
      type={Component === 'button' ? 'button' : undefined}
    >
      <div
        className="movie-card__poster"
        style={movie.posterUrl ? { backgroundImage: `url(${movie.posterUrl})` } : undefined}
        aria-hidden="true"
      />
      <div className="movie-card__content">
        <span className="match">{badge}</span>
        <h3>{movie.title}</h3>
        {directorLabel ? <p className="movie-card__director">Par {directorLabel}</p> : null}
        <p>
          {movie.year} · {movie.genres.join(' / ')}
        </p>
        <div className="movie-card__facts" aria-label="Informations du film">
          <span>{movie.duration}</span>
          {voteLabel ? <span>{voteLabel}</span> : null}
          {movie.originalLanguage ? <span>{movie.originalLanguage.toUpperCase()}</span> : null}
        </div>
      </div>
    </Component>
  )
}

export default MovieCard
