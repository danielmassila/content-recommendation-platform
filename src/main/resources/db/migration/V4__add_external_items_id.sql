ALTER TABLE items ADD COLUMN external_id BIGINT;
CREATE UNIQUE INDEX IF NOT EXISTS uq_items_type_external_id ON items(type, external_id);