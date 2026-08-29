ALTER TABLE users
    ADD COLUMN username VARCHAR(80);

CREATE UNIQUE INDEX idx_users_username_unique
    ON users (username)
    WHERE username IS NOT NULL;
