# Catalogue et import des données

TMDB fournit les informations des films. MovieLens fournit les notes historiques
et les correspondances entre identifiants. Les comptes et notes de l'application
restent dans `users` et `ratings` ; les utilisateurs MovieLens ne sont pas des comptes.

## Parcours à utiliser

Appliquer les migrations avec `make migrate` et construire l'image avec
`make py-build`. Configurer `TMDB_API_KEY` dans `.env` pour récupérer des films.
Les commandes ci-dessous sont exécutées depuis la racine du projet.

### 1. Préparer les fichiers

Placer `links.csv` et `ratings.csv` d'une même distribution MovieLens dans un
répertoire sous `datasets/`. Ce répertoire est monté en lecture seule dans le
conteneur : `datasets/validation-small` devient `/datasets/validation-small`.
Ne pas modifier ces fichiers pendant l'import. Leur empreinte SHA-256 identifie
la version du corpus ; un changement de contenu produit une nouvelle version.

Le téléchargement de latest Full n'est pas encore intégré au parcours. Commencer
par un échantillon : le moteur de recommandation charge encore le corpus en mémoire.
`movies.csv`, les tags et les scores du genome ne sont pas utilisés dans ce parcours.

### 2. Préparer le catalogue TMDB

```bash
make py-sync-catalog DATA_DIR=/datasets/validation-small CATALOG_LIMIT=100 CATALOG_DELAY=0.25
```

La commande lit les `tmdbId` de `links.csv` et crée les films manquants dans
`items` de notre DB. Chaque film est validé dans une transaction distincte, après la requête
HTTP. Les films existants sont ignorés après vérification des identifiants.
Relancer la même commande reprend donc le chargement sans récupérer à nouveau
les films déjà enregistrés. Les métadonnées comprennent les chemins des affiches ;
les images ne sont pas stockées dans PostgreSQL.

`CATALOG_LIMIT` limite le nombre de films demandés à TMDB par exécution, y compris
les réponses 404. Le client peut réessayer une requête en cas de panne temporaire.
`CATALOG_DELAY` espace les demandes de films. Le bilan JSON compte les films chargés,
existants et différés ; il liste les correspondances ambiguës, les IDs MovieLens
sans TMDB et les IDs TMDB introuvables. Conserver ce bilan avec les fichiers source.

Un conflit d'identité ou une erreur autre qu'un 404 arrête la commande avec un code
non nul. Les films précédemment enregistrés restent disponibles pour la reprise.
Les 404 ne sont pas mémorisés en base et seront retentés : augmenter la limite si
ces réponses occupent tout le budget et empêchent d'atteindre les films suivants.
Le bilan JSON est émis seulement à la fin d'une exécution réussie.

Pour actualiser explicitement un film déjà présent, utiliser :

```bash
make py-sync-movie TMDB_ID=603
```

Le chargement du catalogue ne modifie ni les notes ni le statut des imports.

### 3. Charger les notes en staging

```bash
make py-stage DATA_DIR=/datasets/validation-small BATCH_SIZE=10000
```

Conserver le JSON retourné, notamment `import_id` et `dataset_version`.
Le traitement copie et hache les fichiers dans un répertoire temporaire, lit les
notes progressivement et valide chaque lot avec sa progression. Prévoir autant
d'espace temporaire que la taille de `links.csv` et `ratings.csv` réunis.

`staging.movielens_ratings` contient les lignes source typées ;
`staging.movielens_imports` suit la tentative. Le champ `staged_at` signale la fin
du chargement. Le statut reste `loading` jusqu'à publication.
Une erreur interceptée marque la tentative `failed`. Une interruption brutale peut
laisser une tentative `loading` à examiner manuellement. Une nouvelle tentative
recommence depuis le début ; la reprise à la dernière ligne n'est pas implémentée.

### 4. Valider et publier

```bash
make py-publish IMPORT_ID=<uuid-retourne> DATA_DIR=/datasets/validation-small
```

Le traitement vérifie le fichier de correspondances, le nombre de lignes et les
notes contradictoires. Il résout `movieId → tmdbId → items.id`, sans appel réseau.
Les correspondances manquantes ou ambiguës sont comptées comme rejets. Les doublons
identiques sont regroupés ; aucune note résolue signifie un échec de publication.

Les notes acceptées sont écrites dans `public.movielens_ratings` et l'import devient
`ready` dans la même transaction. Les comptes et notes applicatifs ne changent pas.
Relancer une tentative déjà publiée ne modifie rien. Une validation échouée laisse
la tentative disponible pour correction ; elle ne publie aucune modification.

Cette étape verrouille les écritures du catalogue et du staging pendant la
transaction. La lancer hors des autres chargements. Conserver son bilan JSON :
les motifs détaillés de rejet ne sont pas encore persistés en base.

### 5. Calculer et consulter les recommandations

```bash
make py-reco DATASET_VERSION=sha256:<empreinte-retournee>
```

Le moteur utilise uniquement une version publiée et combine ses notes avec celles
de l'application. Il écrit les résultats dans `recommendations` pour les comptes
applicatifs uniquement. Créer un compte dans l'application pour avoir un destinataire.

Pour les recalculs déclenchés depuis l'application, définir dans `.env` :

```dotenv
APP_RECOMMENDATIONS_DATASET_VERSION=sha256:<empreinte-retournee>
```

Redémarrer `make api` après ce changement. Le backend lance actuellement Docker
Compose : il doit disposer du CLI, de l'accès au moteur Docker et du fichier Compose.
Ces capacités ne sont pas fournies par l'image backend actuelle.
Une configuration vide utilise seulement les notes applicatives ; la commande
`make py-reco` exige volontairement une version explicite pour le parcours MovieLens.

## Limites actuelles

- Le registre `ready` est encore dans le staging : ne pas supprimer une tentative
  publiée, même si ses notes finales sont conservées.
- Une publication peut accepter une faible proportion des notes. Les seuils de
  couverture et la politique de republication restent à définir.
- Le calcul charge le corpus en mémoire, même pour un seul utilisateur. Full doit
  attendre des mesures et une adaptation du moteur.
- `make py-eval` évalue les notes applicatives, pas encore le corpus externe.

## Anciens outils

Les raccourcis `py-import`, `py-enrich-tmdb`, `py-download`, `py-all` et `demo-data`
ont été retirés du Makefile. Leurs scripts restent disponibles pour référence,
mais ne font pas partie du parcours décrit ici :

- `jobs.import_dataset` vide les tables et crée des comptes synthétiques.
- `jobs.import_movielens` charge directement sans passer par staging ; il ne rend
  pas une version utilisable par le moteur et refuse de modifier une version publiée.
- `jobs.enrich_tmdb` utilise l'ancien parcours de métadonnées.
- `jobs.download_dataset` cible latest-small ; il ne vérifie pas un téléchargement
  partiel et ne peut pas écrire dans le montage de datasets en lecture seule.

`make reset` reste une commande explicite de suppression des volumes Docker.

## Vérifications

Les tests PostgreSQL utilisent `CATALOG_TEST_DSN` vers une base jetable distincte
et y appliquent les migrations. Ne jamais utiliser la base de l'application pour
ces tests. Le parcours applicatif se vérifie avec un petit échantillon publié :
créer un compte, noter un film, recalculer et consulter les recommandations.
