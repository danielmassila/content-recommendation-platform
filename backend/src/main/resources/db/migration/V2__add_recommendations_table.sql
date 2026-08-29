CREATE TABLE recommendations (
	id BIGSERIAL PRIMARY KEY,
	user_id BIGINT NOT NULL,
	item_id BIGINT NOT NULL,
	score DOUBLE PRECISION NOT NULL,
	rank INT NOT NULL CHECK (rank > 0),
	algo_version VARCHAR(255) NOT NULL,
    reason JSONB NULL,
    run_id UUID NULL,
	generated_at TIMESTAMP NOT NULL DEFAULT NOW(),

	CONSTRAINT fk_reco_users
		FOREIGN KEY (user_id)
		REFERENCES users(id)
		ON DELETE CASCADE,

	CONSTRAINT fk_reco_items
		FOREIGN KEY (item_id)
		REFERENCES items(id)
		ON DELETE CASCADE,

	CONSTRAINT uniq_reco_user_item
		UNIQUE (user_id, item_id)
);

CREATE INDEX IF NOT EXISTS idx_fk_reco_user_rank ON recommendations(user_id, rank);
CREATE INDEX IF NOT EXISTS idx_fk_reco_items ON recommendations(user_id, score DESC);