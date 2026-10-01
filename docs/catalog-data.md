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

## Non-destructive MovieLens import

After applying V8, import historical ratings into `movielens_ratings`:

```bash
docker compose run --rm reco-job python -m jobs.import_movielens
```

Add `--fetch-missing` to retrieve missing catalog films through TMDB (requires
`TMDB_API_KEY`). Without that option, missing films are reported for a later run.
Existing catalog films are not fetched again. Source files default to
`/datasets/raw_data`; `--data-dir` can select another snapshot directory.

The command hashes and parses the same bytes from `links.csv` and `ratings.csv`.
Its JSON output includes the dataset version, per-file SHA-256, inserted/existing
counts, rejected-rating counts and unresolved MovieLens IDs. Preserve this output
with the input files as the import manifest. Exact duplicate input ratings are
collapsed before the reported `ratings_read` count; contradictory duplicates and
invalid rows fail validation. A changed file produces a different dataset version.
Future recommendation reads must explicitly select one snapshot.

The complete import commits together, including new films and mappings. A 404 is
reported as unresolved; temporary API failures and identity conflicts roll back
the operation. Replaying the same files can resolve previously missing films
without duplicating already imported ratings or changing their ingestion date.
MovieLens event timestamps are preserved in UTC. No application users are created,
and application ratings and recommendations are not rewritten.

This first implementation loads the snapshot into memory and writes ratings one
at a time. It targets the small dataset; batching and shorter transactions for
large datasets remain future work. It does not parse tags or change the recommender.
Legacy JSON-only film identities still require the separate audited backfill.

**The old `jobs.import_dataset` / `make py-import` command remains the destructive
legacy demo loader.** Use `jobs.import_movielens` for the new path. Demo-loader
retirement and existing synthetic-user cleanup are separate migration steps.

### Ambiguous MovieLens correspondences

The importer excludes every MovieLens ID involved in contradictory links or a
shared TMDB ID. It never chooses the first row or merges films automatically.
The JSON report lists these IDs under `rejected_links` and counts their ratings
under `ambiguous_link`. Valid films continue through the normal import path.
Malformed CSV rows and conflicts with existing catalog identities still fail.
The standalone `parse_links` function remains strict unless a rejection report
is explicitly supplied. Memory usage and per-rating SQL writes remain to be
improved before loading a large dataset.

## Recommendations with external neighbors

The recommendation CLI accepts `--dataset-version <exact-sha256-version>` to
combine that MovieLens snapshot with application ratings. Positive computation
IDs represent application users; negative IDs represent MovieLens neighbors.
This reversible encoding never changes persisted user IDs. Results are written
only for application users, and popularity statistics use the selected combined
corpus. Unknown or empty snapshots fail before recommendations are rewritten.

Without the flag, the existing application-only behavior remains. For jobs
triggered by Spring, set `APP_RECOMMENDATIONS_DATASET_VERSION` to the exact
`dataset_version` returned by the import. Blank values omit the CLI argument.
Restart the local backend (`make api`) after changing `.env`; for a containerized
backend recreate it with `docker compose up -d --build backend`. The variable is
passed for both targeted and global recalculations. No snapshot is chosen
implicitly, and an unknown snapshot fails the Python job. Offline evaluation
of the external corpus remains separate follow-up work.

This setting configures the command only: the existing process launcher still
requires Docker CLI/Compose, access to the Docker engine and the Compose file.
It does not provision those capabilities in the backend container.

The next dataset will be **MovieLens latest Full (`ml-latest.zip`)**. The
[official README](https://files.grouplens.org/datasets/movielens/ml-latest-README.html)
describes 33,832,162 ratings, 2,328,315 tag applications and 86,537 movies,
generated July 20, 2023. Keep an archive checksum since `latest` can change.
Tags and genome scores are not consumed yet. Neither the importer nor the
in-memory user-neighbor engine is ready for the full volume: streaming imports,
batched writes and bounded recommendation computations must precede loading it.

## Staging and published data

V9 introduces a separate `staging` schema in the same PostgreSQL database.
Here, "production" means validated data consumed by the application, not a
separate production deployment. Existing `public.items`, `public.ratings` and
`public.movielens_ratings` retain their names and contracts.

- `staging.movielens_imports` identifies each attempt by UUID and records its
  snapshot, source hashes, counters, status and timestamps. Failed attempts can
  be retried under a new UUID; concurrent loading attempts for one snapshot are
  blocked by a unique index.
- `staging.movielens_ratings` stores typed source rows before movie-ID resolution.
  Rows reference source line numbers, allowing contradictory duplicate ratings
  to be detected before publication rather than silently overwritten.
- Removing an attempt removes its staging rows, never published ratings.

This is the schema-only preparatory step. The existing importer still writes
published ratings in one transaction, and existing snapshots are not retroactively
marked ready. Subsequent steps will implement streaming/COPY loading, validation,
atomic publication and a published-snapshot readiness check in the recommender.
The new status field alone does not authorize or perform publication. Staging
separation is logical; separate database roles/permissions are not introduced yet.

### Batched staging loader (V10)

`python -m jobs.stage_movielens --data-dir /datasets/validation-small --batch-size 10000`
loads only staging. The loader copies and hashes source files into a temporary
local directory, streams ratings, and commits each COPY batch together with its
progress counter. Temporary disk space roughly equal to the two CSV files is
required; rating memory is bounded by batch size. Source files must remain stable
while the initial copy is made. Keep original files for subsequent mapping checks.

`staged_at` records completed loading, but status stays `loading` until validation
and publication are implemented. Accepted/rejected counts are reserved for that
validation. Duplicate source rows remain in staging. On a caught failure, the
current batch rolls back and the attempt becomes `failed`; committed staging rows
remain for inspection. A hard process kill or lost DB connection may leave a
`loading` attempt requiring manual review. Failed attempts can be restarted from
the beginning with a new UUID; exact-line resume is not implemented. No production
ratings, accounts or catalogue films are changed by this command.

### Validate and publish staging

After loading and preparing the TMDB catalogue, run:

```bash
docker compose run --rm reco-job python -m jobs.publish_movielens \
  --import-id <UUID-returned-by-staging> --links /datasets/validation-small/links.csv
```

Publication verifies the links checksum and staged row count, rejects conflicting
notes, resolves source movie IDs, and counts missing/ambiguous mappings as rejected
rows. It performs no TMDB requests. Identical duplicates count as accepted source
rows but produce one published note. Zero resolved notes blocks publication.

Replacing that snapshot's published ratings and setting `ready` occur in one
transaction. Other snapshots and application ratings stay unchanged. Repeating
publication of an already-ready attempt is a no-op. A validation failure leaves
staging in `loading` for review, with no published changes. The transaction locks
staged rows and catalogue writes for consistency; this first version serializes
publication against staging writes. Run it in a maintenance window.

This command provides atomic publication, but the old direct importer still
exists and the recommender's readiness gate is a subsequent step. Do not infer
that all legacy snapshots have been validated merely because their rows exist.

### Recommender publication gate

A configured snapshot must have a `ready` attempt in
`staging.movielens_imports` before its ratings can be used. Unpublished legacy
snapshots must pass through staging and publication first; their existing rows
alone do not authorize computation. Missing/unready snapshots fail before any
recommendations are rewritten. Application-only mode (no snapshot configured)
remains available. The legacy direct importer now refuses to modify a published
snapshot, using the same transaction lock as publication.

Validation sequence: apply migrations through V10, stage the small sample,
publish using its returned import UUID and matching links file, configure the
returned dataset version in the backend, then trigger recalculation. Loading and
publication do not change the checksum-based dataset version for identical files.
