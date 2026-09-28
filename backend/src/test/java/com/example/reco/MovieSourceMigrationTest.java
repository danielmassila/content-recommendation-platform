package com.example.reco;

import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.dao.DataIntegrityViolationException;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.junit.jupiter.api.Assertions.*;

@Testcontainers(disabledWithoutDocker = true)
class MovieSourceMigrationTest {
    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");

    private JdbcTemplate jdbc;

    @BeforeEach
    void resetDatabase() {
        jdbc = new JdbcTemplate(new DriverManagerDataSource(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword()));
        // This class owns a disposable Testcontainers database; Flyway cleans public only.
        jdbc.execute("DROP SCHEMA IF EXISTS staging CASCADE");
        Flyway flyway = flyway(null);
        flyway.clean();
    }

    private Flyway flyway(String target) {
        var config = Flyway.configure()
                .dataSource(POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword())
                .cleanDisabled(false);
        if (target != null) {
            config.target(target);
        }
        return config.load();
    }

    @Test
    void upgradesExistingDataWithoutChangingIdsOrInferringSourceIds() {
        flyway("6").migrate();
        Long userId = jdbc.queryForObject(
                "INSERT INTO users (email) VALUES ('existing@example.com') RETURNING id", Long.class);
        Long itemId = jdbc.queryForObject("""
                INSERT INTO items (title, type, external_id, metadata)
                VALUES ('Existing movie', 'MOVIE', 2571, '{"tmdbId":603}') RETURNING id
                """, Long.class);
        jdbc.update("INSERT INTO ratings (user_id, item_id, rating) VALUES (?, ?, 4.5)", userId, itemId);
        jdbc.update("""
                INSERT INTO recommendations (user_id, item_id, score, rank, algo_version)
                VALUES (?, ?, 0.8, 1, 'existing')
                """, userId, itemId);

        flyway(null).migrate();
        flyway(null).validate();

        var item = jdbc.queryForMap("SELECT * FROM items WHERE id = ?", itemId);
        assertEquals(2571L, item.get("external_id"));
        assertEquals("Existing movie", item.get("title"));
        assertNull(item.get("tmdb_id"));
        assertNull(item.get("movielens_id"));
        assertNull(item.get("imdb_id"));
        assertNull(item.get("tmdb_last_synced_at"));
        assertEquals("603", jdbc.queryForObject(
                "SELECT metadata->>'tmdbId' FROM items WHERE id = ?", String.class, itemId));
        assertEquals(itemId, jdbc.queryForObject("SELECT item_id FROM ratings WHERE user_id = ?", Long.class, userId));
        assertEquals(itemId, jdbc.queryForObject("SELECT item_id FROM recommendations WHERE user_id = ?", Long.class, userId));
    }

    @Test
    void freshDatabaseAllowsLegacyAndTmdbOnlyMoviesButRejectsDuplicateMovieIds() {
        flyway(null).migrate();
        insert("MOVIE", null, null, null);
        insert("MOVIE", null, null, null);
        Long tmdbOnlyId = insert("MOVIE", 603L, null, "tt0133093");
        assertNull(jdbc.queryForObject("SELECT movielens_id FROM items WHERE id = ?", Long.class, tmdbOnlyId));
        assertEquals("tt0133093", jdbc.queryForObject("SELECT imdb_id FROM items WHERE id = ?", String.class, tmdbOnlyId));
        assertThrows(DataIntegrityViolationException.class, () -> insert("MOVIE", 603L, null, null));
        insert("MOVIE", 604L, 2571L, null);
        assertThrows(DataIntegrityViolationException.class, () -> insert("MOVIE", 605L, 2571L, null));
        // Movie uniqueness does not reserve identifiers for other item types.
        insert("BOOK", 603L, 2571L, null);
    }

    @Test
    void rejectsInvalidExternalIdentifiers() {
        flyway(null).migrate();
        assertThrows(DataIntegrityViolationException.class, () -> insert("MOVIE", 0L, null, null));
        assertThrows(DataIntegrityViolationException.class, () -> insert("MOVIE", -1L, null, null));
        assertThrows(DataIntegrityViolationException.class, () -> insert("MOVIE", null, 0L, null));
        assertThrows(DataIntegrityViolationException.class, () -> insert("MOVIE", null, -1L, null));
        assertThrows(DataIntegrityViolationException.class, () -> insert("MOVIE", null, null, "0133093"));
        assertThrows(DataIntegrityViolationException.class, () -> insert("MOVIE", null, null, "tt"));
    }

    private Long insert(String type, Long tmdbId, Long movielensId, String imdbId) {
        return jdbc.queryForObject("""
                INSERT INTO items (title, type, tmdb_id, movielens_id, imdb_id)
                VALUES ('Test item', ?, ?, ?, ?) RETURNING id
                """, Long.class, type, tmdbId, movielensId, imdbId);
    }

    @Test
    void externalRatingsDoNotRequireOrBelongToFromApplicationUser() {
        flyway("7").migrate();
        Long itemId = insert("MOVIE", 603L, null, null);
        Long userId = jdbc.queryForObject(
                "INSERT INTO users (email) VALUES ('real@example.com') RETURNING id", Long.class);
        jdbc.update("INSERT INTO ratings (user_id, item_id, rating) VALUES (?, ?, 3)", userId, itemId);
        flyway(null).migrate();
        flyway(null).validate();
        assertEquals(1, jdbc.queryForObject("SELECT count(*) FROM ratings", Integer.class));
        assertEquals(0, jdbc.queryForObject("SELECT count(*) FROM movielens_ratings", Integer.class));

        insertExternalRating("snapshot-a", userId, itemId, "4.5");
        insertExternalRating("snapshot-a", 999999L, itemId, "0.5");
        jdbc.update("DELETE FROM users WHERE id = ?", userId);
        assertEquals(2, jdbc.queryForObject("SELECT count(*) FROM movielens_ratings", Integer.class));
        assertEquals(0, jdbc.queryForObject("SELECT count(*) FROM users", Integer.class));
        assertThrows(DataIntegrityViolationException.class,
                () -> jdbc.update("DELETE FROM items WHERE id = ?", itemId));
    }

    @Test
    void externalRatingsAreUniqueWithinEachSnapshotAndKeepSourceTime() {
        flyway(null).migrate();
        Long itemId = insert("MOVIE", 603L, null, null);
        insertExternalRating("snapshot-a", 42L, itemId, "5");
        assertThrows(DataIntegrityViolationException.class,
                () -> insertExternalRating("snapshot-a", 42L, itemId, "4"));
        insertExternalRating("snapshot-b", 42L, itemId, "4");
        assertEquals(2, jdbc.queryForObject("SELECT count(*) FROM movielens_ratings", Integer.class));
        assertEquals(true, jdbc.queryForObject("""
                SELECT bool_and(rated_at = TIMESTAMPTZ '2018-01-01 12:00:00+02'
                    AND ingested_at > rated_at)
                FROM movielens_ratings
                """, Boolean.class));
    }

    @Test
    void externalRatingsRejectInvalidValuesAndMissingReferences() {
        flyway(null).migrate();
        Long itemId = insert("MOVIE", 603L, null, null);
        for (String rating : new String[]{"0", "5.5", "4.49", "NaN"}) {
            assertThrows(DataIntegrityViolationException.class,
                    () -> insertExternalRating("snapshot-a", 42L, itemId, rating));
        }
        assertThrows(DataIntegrityViolationException.class,
                () -> insertExternalRating("snapshot-a", 0L, itemId, "4"));
        assertThrows(DataIntegrityViolationException.class,
                () -> insertExternalRating(" ", 42L, itemId, "4"));
        assertThrows(DataIntegrityViolationException.class,
                () -> insertExternalRating("snapshot-a", 42L, -1L, "4"));
        insertExternalRating("snapshot-a", 42L, itemId, "4");
        for (String column : new String[]{"dataset_version", "movielens_user_id", "item_id",
                "rating", "rated_at", "ingested_at"}) {
            assertThrows(DataIntegrityViolationException.class,
                    () -> jdbc.update("UPDATE movielens_ratings SET " + column + " = NULL"));
        }
    }

    private void insertExternalRating(String version, Long userId, Long itemId, String rating) {
        jdbc.update("""
                INSERT INTO movielens_ratings (dataset_version, movielens_user_id, item_id, rating, rated_at)
                VALUES (?, ?, ?, CAST(? AS NUMERIC), TIMESTAMPTZ '2018-01-01 10:00:00+00')
                """, version, userId, itemId, rating);
    }
}
