package com.example.reco;

import com.example.reco.model.Item;
import com.example.reco.model.ItemType;
import jakarta.persistence.EntityManager;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest
@Testcontainers(disabledWithoutDocker = true)
@ActiveProfiles("test")
class RecoApplicationTests {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private EntityManager entityManager;

    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("reco_test")
            .withUsername("reco_test")
            .withPassword("reco_test");

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("app.jwt.secret", () -> "test-only-secret-that-is-long-enough-for-tests");
    }

    @Test
    void contextLoads() {
        Integer migrationCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM flyway_schema_history WHERE success = true",
                Integer.class
        );
        Integer recommendationTableCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'recommendations'",
                Integer.class
        );

        org.junit.jupiter.api.Assertions.assertTrue(migrationCount >= 8);
        org.junit.jupiter.api.Assertions.assertEquals(1, recommendationTableCount);
    }

    @Test
    @Transactional
    void movieSourceIdentifiersRoundTripThroughJpa() {
        Item movie = new Item("The Matrix", ItemType.MOVIE, "{}");
        movie.setTmdbId(603L);
        movie.setImdbId("tt0133093");
        movie.setMovielensId(2571L);
        Instant syncedAt = Instant.parse("2026-09-28T10:00:00Z");
        movie.setTmdbLastSyncedAt(syncedAt);
        entityManager.persist(movie);
        entityManager.flush();
        Long internalId = movie.getId();
        entityManager.clear();

        Item loaded = entityManager.find(Item.class, internalId);
        org.junit.jupiter.api.Assertions.assertEquals(603L, loaded.getTmdbId());
        org.junit.jupiter.api.Assertions.assertEquals("tt0133093", loaded.getImdbId());
        org.junit.jupiter.api.Assertions.assertEquals(2571L, loaded.getMovielensId());
        org.junit.jupiter.api.Assertions.assertEquals(syncedAt, loaded.getTmdbLastSyncedAt());
    }

}
