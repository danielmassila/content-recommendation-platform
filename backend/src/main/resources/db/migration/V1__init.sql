CREATE TABLE users (
	id BIGSERIAL PRIMARY KEY,
	email VARCHAR(255) UNIQUE NOT NULL,
	password_hash VARCHAR(255),
	created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE items (
	id BIGSERIAL PRIMARY KEY,
	title VARCHAR(255) NOT NULL,
	type VARCHAR(255) NOT NULL,
	metadata JSONB,
	created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE ratings (
	id BIGSERIAL PRIMARY KEY,
	user_id BIGINT NOT NULL,
	item_id BIGINT NOT NULL,
	rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
	created_at TIMESTAMP NOT NULL DEFAULT NOW(),

	CONSTRAINT fk_ratings_users
		FOREIGN KEY (user_id)
		REFERENCES users(id)
		ON DELETE CASCADE,

	CONSTRAINT fk_ratings_items
		FOREIGN KEY (item_id)
		REFERENCES items(id)
		ON DELETE CASCADE,

	CONSTRAINT uniq_rating
		UNIQUE (user_id, item_id)
);

CREATE INDEX idx_fk_ratings_user ON ratings(user_id);
CREATE INDEX idx_fk_ratings_items ON ratings(item_id);
CREATE INDEX idx_items_type ON items(type);