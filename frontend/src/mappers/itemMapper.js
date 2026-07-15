const posterTones = ['mint', 'blue', 'peach', 'amber', 'violet', 'slate', 'sand', 'steel', 'green']

export const parseItemMetadata = (metadata) => {
  if (!metadata) {
    return {}
  }

  if (typeof metadata !== 'string') {
    return metadata
  }

  try {
    return JSON.parse(metadata)
  } catch {
    return {}
  }
}

const normalizeGenres = (metadata, itemType) => {
  if (Array.isArray(metadata.genres)) {
    return metadata.genres
  }

  if (typeof metadata.genres === 'string') {
    return metadata.genres.split(',').map((genre) => genre.trim())
  }

  if (typeof metadata.genre === 'string') {
    return [metadata.genre]
  }

  return [itemType ?? 'Film']
}

const toMatchPercent = (score) => {
  if (typeof score !== 'number') {
    return 0
  }

  return Math.round(score <= 1 ? score * 100 : score)
}

export const toMovieCard = (item, recommendation, index = 0, rating) => {
  const metadata = parseItemMetadata(item?.metadata)
  const tmdb = metadata.tmdb ?? {}

  return {
    id: item?.id,
    title: item?.title ?? 'Titre inconnu',
    year: metadata.year ?? metadata.releaseYear ?? 'Année inconnue',
    duration: metadata.duration ?? (metadata.runtime ? `${metadata.runtime} min` : 'Durée inconnue'),
    genres: normalizeGenres(metadata, item?.type),
    match: recommendation ? toMatchPercent(recommendation.score) : 0,
    description:
      recommendation?.reason ??
      metadata.overview ??
      metadata.description ??
      'Les informations détaillées ne sont pas encore disponibles pour ce contenu.',
    posterUrl:
      tmdb.posterPath && tmdb.imageBaseUrl
        ? `${tmdb.imageBaseUrl}/w342${tmdb.posterPath}`
        : undefined,
    posterTone: posterTones[index % posterTones.length],
    item,
    rating,
    recommendation,
  }
}
