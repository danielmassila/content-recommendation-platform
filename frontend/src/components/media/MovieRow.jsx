import MovieCard from './MovieCard'

const MovieRow = ({ row }) => {
  return (
    <section className="movie-row" aria-labelledby={`${row.id}-title`}>
      <h2 id={`${row.id}-title`}>{row.title}</h2>
      <div className="movie-row__scroller">
        {row.items.map((movie) => (
          <MovieCard key={movie.id} movie={movie} />
        ))}
      </div>
    </section>
  )
}

export default MovieRow
