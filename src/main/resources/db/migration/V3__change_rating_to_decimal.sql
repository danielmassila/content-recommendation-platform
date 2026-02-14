ALTER TABLE ratings
  ALTER COLUMN rating TYPE NUMERIC(2,1)
  USING rating::NUMERIC(2,1);

ALTER TABLE ratings
  DROP CONSTRAINT IF EXISTS ratings_rating_check;

ALTER TABLE ratings
  ADD CONSTRAINT ratings_rating_check
  CHECK (rating >= 0.5 AND rating <= 5.0 AND (rating * 2) = floor(rating * 2));
