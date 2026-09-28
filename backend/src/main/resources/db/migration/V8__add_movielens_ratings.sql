-- External users belong to a dataset snapshot, never to the application users table.
CREATE TABLE movielens_ratings (
    dataset_version TEXT NOT NULL CHECK (btrim(dataset_version) <> ''),
    movielens_user_id BIGINT NOT NULL CHECK (movielens_user_id > 0),
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
    -- No fixed scale: reject invalid precision rather than silently rounding it
    rating NUMERIC NOT NULL
        CHECK (rating >= 0.5 AND rating <= 5 AND rating * 2 = floor(rating * 2)),
    rated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dataset_version, movielens_user_id, item_id)
);

CREATE INDEX idx_movielens_ratings_item ON movielens_ratings (item_id);
