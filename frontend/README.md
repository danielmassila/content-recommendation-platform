# Frontend

Interface React/Vite de l'application de recommandation de films.

## Commandes

```bash
npm install
npm run dev
npm run build
npm run lint
```

## Structure

```text
src/
  components/   composants UI réutilisables
  data/         données temporaires de développement
  hooks/        hooks applicatifs à brancher progressivement
  pages/        pages principales de l'application
  services/     accès API et intégration backend
  styles/       tokens et fondations visuelles
```

## Hooks prévus

- `useAuth` : session utilisateur, connexion, déconnexion.
- `useMovieCatalog` : catalogue, filtres, recherche.
- `usePreferences` : préférences initiales et mise à jour.
- `useRecommendations` : sélection du soir et recommandations personnalisées.
- `useUserProfile` : profil, statistiques et notes récentes.

Ces hooks sont volontairement non implémentés pour le moment. Ils servent de points d'entrée clairs pour brancher le backend sans mélanger la logique métier avec les pages.

## Style

Les couleurs, rayons, espacements et dimensions principales sont centralisés dans `src/styles/tokens.css`.

Le fichier `src/index.css` doit surtout contenir les classes concrètes des composants et des pages. Quand le thème change, commencer par modifier les tokens.

## Commits

Utiliser des commits conventionnels en anglais, courts et explicites :

```text
feat: add app routing
chore: add api client setup
docs: document frontend structure
```

Garder les commits assez petits : une intention claire par commit.
