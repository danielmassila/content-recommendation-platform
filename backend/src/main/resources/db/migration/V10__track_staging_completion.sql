-- Loading completion is distinct from validation/publication (status = ready).
ALTER TABLE staging.movielens_imports ADD COLUMN staged_at TIMESTAMPTZ;
