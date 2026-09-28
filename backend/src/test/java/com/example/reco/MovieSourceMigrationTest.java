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
        Flyway flyway = flyway(null);
        flyway.clean();
        jdbc = new JdbcTemplate(new DriverManagerDataSource(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword()));
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
}
