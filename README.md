# Content Recommendation Platform

This project is a backend-oriented content recommendation platform, designed to explore how recommendation systems can
be integrated into a real-world software architecture. For this first version, I decided to focus on movie
recommendation, but my initial goal was to mix the content recommendations, with books, songs and movies, so that I
solve a problem that I truly face: finding interesting new content to discover.

## Project Overview

Throughout this project, I wanted to explore how recommendation systems can be integrated into a real-world software
architecture.

This first version focuses on movie recommendations, but my initial goal was to mix the content recommendations, with
books, songs and movies, so that I solve a problem that I truly face: finding interesting new content to discover.

Rather than building a UI-centric application, I deliberately focused on:

- System design
- Data flow
- Architectural trade-offs
- Engineering constraints

I built the whole project based on an end-to-end recommendation pipeline:
data ingestion → storage → computation → API exposure.

## Architecture

The system is composed of:

- **`backend/`** Java (Spring Boot) REST API
- **`frontend/`** React interface
- **`reco-ml/`** Python recommendation engine and data jobs
- **PostgreSQL** shared database
- **Docker Compose** for orchestration

The detailed architecture is available here:

👉 `docs/architecture.md`

---

## Recommendation Strategy

Hybrid model:

1. Bayesian-weighted popularity baseline
2. User-based collaborative filtering (using cosine similarity)
3. Dynamic hybrid blending based on profile maturity

Full explanation:
👉 `docs/recommendation.md`

---

## Quick Start

```bash
git clone <repo>
cd content-recommendation-platform
make demo
```

## Data enrichment

MovieLens is used as the local recommendation dataset. The download/import pipeline stores:

- users from MovieLens user ids
- movies in `items`
- ratings in `ratings`
- external ids from `links.csv` in `items.metadata`

TMDB is optional and should be used as an enrichment source, not as the application database.

```bash
cp .env.example .env
# fill TMDB_API_KEY in .env
make py-enrich-tmdb
```

The TMDB job enriches existing `items.metadata` with poster paths, overview, release date,
runtime, popularity and vote averages when a `tmdbId` is available.

The rationale, failure behavior and scaling boundary of this hybrid local/API model are
documented in [`docs/catalog-data.md`](docs/catalog-data.md).

## Local administrator

Every registered account starts with the `USER` role. For local development, promote a
trusted account explicitly after registration:

```bash
docker compose exec db psql -U reco_user -d reco_db \
  -c "UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com';"
```

Restart the session after changing a role. Administrative routes are protected by the
backend; hiding the development page in the frontend is only a usability measure.

Production must run Spring with the `prod` profile and provide `APP_JWT_SECRET` and
`APP_CORS_ALLOWED_ORIGINS` through its secret/configuration manager.
