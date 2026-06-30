import MovieCard from '../components/media/MovieCard'
import MovieRow from '../components/media/MovieRow'
import Button from '../components/ui/Button'
import { featuredPick, movieRows } from '../data/movies'

const DiscoveryPage = () => {
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

      {movieRows.map((row) => (
        <MovieRow key={row.id} row={row} />
      ))}
    </section>
  )
}

export default DiscoveryPage
