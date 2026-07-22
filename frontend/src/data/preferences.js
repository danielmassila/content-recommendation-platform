export const preferenceTypes = [
  {
    id: 'genre',
    label: 'Genre',
    question: 'Quels genres te donnent envie de lancer un film ?',
    placeholder: 'Ex. thriller, animation, drame...',
    suggestions: ['Thriller', 'Drame', 'Science-fiction', 'Comedie', 'Animation', 'Crime', 'Romance', 'Horreur'],
  },
  {
    id: 'movie',
    label: 'Film',
    question: 'Quels films aimerais-tu retrouver dans l’esprit ?',
    placeholder: 'Ex. Parasite, Heat, Arrival...',
    suggestions: ['Parasite', 'Heat', 'Arrival', 'Whiplash', 'Drive', 'Inception', 'Her', 'Dune'],
  },
  {
    id: 'person',
    label: 'Acteur / realisatrice',
    question: 'Quelles personnes te donnent confiance dans un film ?',
    placeholder: 'Ex. Denis Villeneuve, Saoirse Ronan...',
    suggestions: [
      'Denis Villeneuve',
      'Christopher Nolan',
      'Bong Joon-ho',
      'Greta Gerwig',
      'Saoirse Ronan',
      'Ryan Gosling',
      'Viola Davis',
      'Mads Mikkelsen',
    ],
  },
]

export const getPreferenceType = (typeId) => {
  return preferenceTypes.find((type) => type.id === typeId) ?? preferenceTypes[0]
}
