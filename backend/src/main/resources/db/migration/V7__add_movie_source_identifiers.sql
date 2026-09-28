-- Nullable columns preserve existing items until their source IDs are audited.
ALTER TABLE items
    ADD COLUMN tmdb_id BIGINT,
    ADD COLUMN imdb_id VARCHAR(32),
    ADD COLUMN movielens_id BIGINT,
    ADD COLUMN tmdb_last_synced_at TIMESTAMP WITH TIME ZONE,
    ADD CONSTRAINT ck_items_tmdb_id_positive CHECK (tmdb_id > 0),
    ADD CONSTRAINT ck_items_movielens_id_positive CHECK (movielens_id > 0),
    ADD CONSTRAINT ck_items_imdb_id_format CHECK (imdb_id ~ '^tt[0-9]+$');

CREATE UNIQUE INDEX uq_items_movie_tmdb_id
    ON items (tmdb_id) WHERE type = 'MOVIE';

CREATE UNIQUE INDEX uq_items_movie_movielens_id
    ON items (movielens_id) WHERE type = 'MOVIE';
