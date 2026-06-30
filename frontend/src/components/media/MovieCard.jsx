const MovieCard = ({ movie, compact = false }) => {
  return (
    <article className={`movie-card movie-card--${movie.posterTone} ${compact ? 'movie-card--compact' : ''}`}>
      <div className="movie-card__poster" aria-hidden="true" />
      <div className="movie-card__content">
        <span className="match">{movie.match}% pertinent</span>
        <h3>{movie.title}</h3>
        <p>
          {movie.year} · {movie.genres.join(' / ')}
        </p>
      </div>
    </article>
  )
}

export default MovieCard
