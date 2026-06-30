export const featuredPick = {
  id: 'scarface',
  title: 'Scarface',
  year: 1983,
  duration: '2h50',
  genres: ['Crime', 'Drame'],
  match: 94,
  description:
    'Un classique intense pour une soirée où tu veux quelque chose de nerveux, culte et très incarné.',
  posterTone: 'coral',
}

export const movieRows = [
  {
    id: 'recommended',
    title: 'Recommandé pour toi',
    items: [
      { id: 'parasite', title: 'Parasite', year: 2019, genres: ['Thriller', 'Drame'], match: 98, posterTone: 'mint' },
      { id: 'arrival', title: 'Premier Contact', year: 2016, genres: ['Sci-fi'], match: 91, posterTone: 'blue' },
      { id: 'her', title: 'Her', year: 2013, genres: ['Romance'], match: 88, posterTone: 'peach' },
      { id: 'whiplash', title: 'Whiplash', year: 2014, genres: ['Drame'], match: 86, posterTone: 'amber' },
      { id: 'drive', title: 'Drive', year: 2011, genres: ['Action'], match: 84, posterTone: 'violet' },
      { id: 'inception', title: 'Inception', year: 2010, genres: ['Sci-fi'], match: 82, posterTone: 'slate' },
    ],
  },
  {
    id: 'recent',
    title: 'Notes récentes',
    items: [
      { id: 'dune', title: 'Dune', year: 2021, genres: ['Aventure'], match: 90, posterTone: 'sand' },
      { id: 'heat', title: 'Heat', year: 1995, genres: ['Polar'], match: 89, posterTone: 'steel' },
      { id: 'social-network', title: 'The Social Network', year: 2010, genres: ['Biopic'], match: 85, posterTone: 'green' },
    ],
  },
]

export const preferenceOptions = [
  { id: 'thriller', label: 'Thriller', hint: 'Tension, enquête, twist' },
  { id: 'drama', label: 'Drame', hint: 'Personnages forts' },
  { id: 'scifi', label: 'Science-fiction', hint: 'Concepts et mondes' },
  { id: 'comedy', label: 'Comédie', hint: 'Léger et efficace' },
]

export const profileStats = [
  { label: 'Films notés', value: '128' },
  { label: 'Genre préféré', value: 'Drame' },
  { label: 'Dernière note', value: '4.5' },
]
