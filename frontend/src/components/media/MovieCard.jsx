const MovieCard = ({ movie, compact = false, onSelect }) => {
  const badge = movie.rating ? `${movie.rating.rating}/5` : `${movie.match}% pertinent`
  const Component = onSelect ? 'button' : 'article'

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
        <p>
          {movie.year} · {movie.genres.join(' / ')}
        </p>
      </div>
    </Component>
  )
}

export default MovieCard
