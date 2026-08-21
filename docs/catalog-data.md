# Catalog data strategy

The application keeps a local catalog because ratings and recommendations require stable internal item identifiers.
An external movie API cannot replace this relational core without making the recommendation pipeline dependent on
network availability and third-party identifier semantics.

MovieLens remains the reproducible seed dataset. TMDB is an optional enrichment provider for posters, descriptions,
credits and public popularity signals. Provider payloads are normalized into `items.metadata`; the frontend never
calls TMDB directly and the API key therefore stays server-side.

## Data flow

1. `make py-download` downloads the reproducible MovieLens source.
2. `make py-import` creates stable local items and ratings.
3. `make py-enrich-tmdb` enriches eligible movies in bounded batches.
4. Spring exposes a paginated catalog independently of the enrichment provider.

The enrichment job retries HTTP 429 and 5xx responses with backoff, commits progress in configurable batches and
records `tmdbEnrichedAt`. A failed enrichment leaves the core movie usable with its MovieLens metadata.

## Scaling boundary

`TMDB_ENRICH_LIMIT`, `TMDB_ENRICH_BATCH_SIZE` and `TMDB_REQUEST_DELAY_SECONDS` bound each run. For horizontally scaled
production workloads, move enrichment requests to a durable queue and use a distributed rate limiter before adding
multiple workers.
