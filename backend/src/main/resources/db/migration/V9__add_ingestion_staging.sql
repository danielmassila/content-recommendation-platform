-- Staging is an ingestion area, not a separate deployment environment.
-- Existing public tables remain the application-facing (published) data.
CREATE SCHEMA staging;

CREATE TABLE staging.movielens_imports (
    id UUID PRIMARY KEY,
    dataset_version TEXT NOT NULL CHECK (btrim(dataset_version) <> ''),
    status TEXT NOT NULL DEFAULT 'loading'
        CHECK (status IN ('loading', 'failed', 'ready')),
    source_hashes JSONB NOT NULL CHECK (jsonb_typeof(source_hashes) = 'object'),
    rows_read BIGINT NOT NULL DEFAULT 0 CHECK (rows_read >= 0),
    rows_accepted BIGINT NOT NULL DEFAULT 0 CHECK (rows_accepted >= 0),
    rows_rejected BIGINT NOT NULL DEFAULT 0 CHECK (rows_rejected >= 0),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    error_message TEXT,
    CHECK (rows_accepted + rows_rejected <= rows_read),
    CHECK ((status = 'loading' AND finished_at IS NULL)
        OR (status IN ('failed', 'ready') AND finished_at IS NOT NULL)),
    CHECK (status <> 'ready' OR rows_accepted + rows_rejected = rows_read)
);

-- Permit retry attempts after failure, but only one loader for a snapshot.
CREATE UNIQUE INDEX uq_movielens_loading_snapshot
    ON staging.movielens_imports(dataset_version) WHERE status = 'loading';

CREATE TABLE staging.movielens_ratings (
    import_id UUID NOT NULL REFERENCES staging.movielens_imports(id) ON DELETE CASCADE,
    source_line BIGINT NOT NULL CHECK (source_line >= 2),
    movielens_user_id BIGINT NOT NULL CHECK (movielens_user_id > 0),
    movielens_movie_id BIGINT NOT NULL CHECK (movielens_movie_id > 0),
    rating NUMERIC NOT NULL
        CHECK (rating >= 0.5 AND rating <= 5 AND rating * 2 = floor(rating * 2)),
    rated_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (import_id, source_line)
);

-- Keep duplicate source rows for validation before publication.
CREATE INDEX idx_staging_movielens_user_movie
    ON staging.movielens_ratings(import_id, movielens_user_id, movielens_movie_id);
