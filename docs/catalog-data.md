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

## Explicit TMDB movie ingestion

After applying the source-identifier migrations (V7 and later), a single film can
be created or refreshed independently of MovieLens:

```bash
docker compose run --rm reco-job python -m jobs.sync_tmdb_movie 603
```

This requires `TMDB_API_KEY` and a rebuilt job image (`docker compose build reco-job`)
if its dependencies are not installed yet. The command always refreshes the requested
film; automatic freshness-based selection is not implemented yet.

The loader keeps the internal item ID, uses the unique movie `tmdb_id` index for
concurrent upserts, and preserves existing MovieLens IDs and application ratings.
An absent IMDb ID does not clear the existing one; a contradictory IMDb ID blocks
the update. Provider metadata is refreshed while unrelated metadata keys are kept.
Poster paths remain nullable and use the existing frontend metadata contract.

Legacy rows with matching TMDB IDs only in JSON block ingestion until an audited
backfill assigns their explicit identifiers. This command does not perform that
backfill. The existing enrichment command remains on its legacy path for now.

The PostgreSQL integration tests require `CATALOG_TEST_DSN` pointing to a fresh,
disposable database: they apply repository migrations and insert test data.
Never point this variable at the application's database.

## Scaling boundary

`TMDB_ENRICH_LIMIT`, `TMDB_ENRICH_BATCH_SIZE` and `TMDB_REQUEST_DELAY_SECONDS` bound each run. For horizontally scaled
production workloads, move enrichment requests to a durable queue and use a distributed rate limiter before adding
multiple workers.
