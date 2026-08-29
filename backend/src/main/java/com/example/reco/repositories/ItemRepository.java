package com.example.reco.repositories;

import com.example.reco.model.Item;
import com.example.reco.model.ItemType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ItemRepository extends JpaRepository<Item, Long> {
    @Query(
            value = """
                    SELECT i.*
                    FROM items i
                    WHERE (:itemType = '' OR i.type = :itemType)
                      AND (:query = '' OR LOWER(i.title) LIKE LOWER(CONCAT('%', :query, '%')))
                      AND (:genre = '' OR EXISTS (
                          SELECT 1
                          FROM jsonb_array_elements_text(
                              CASE
                                  WHEN jsonb_typeof(i.metadata -> 'genres') = 'array'
                                      THEN i.metadata -> 'genres'
                                  ELSE '[]'::jsonb
                              END
                          ) AS item_genre(value)
                          WHERE LOWER(item_genre.value) = LOWER(:genre)
                      ))
                      AND (:year IS NULL OR COALESCE(i.metadata ->> 'year', i.metadata ->> 'releaseYear') = CAST(:year AS text))
                      AND (:minVote IS NULL OR COALESCE(NULLIF(i.metadata -> 'tmdb' ->> 'voteAverage', '')::double precision, 0) >= :minVote)
                      AND (
                          :ratingStatus = 'all'
                          OR (:ratingStatus = 'rated' AND CAST(:userId AS bigint) IS NOT NULL AND EXISTS (
                              SELECT 1 FROM ratings r WHERE r.item_id = i.id AND r.user_id = CAST(:userId AS bigint)
                          ))
                          OR (:ratingStatus = 'unrated' AND (
                              CAST(:userId AS bigint) IS NULL OR NOT EXISTS (
                                  SELECT 1 FROM ratings r WHERE r.item_id = i.id AND r.user_id = CAST(:userId AS bigint)
                              )
                          ))
                      )
                    ORDER BY LOWER(i.title), i.id
                    """,
            countQuery = """
                    SELECT COUNT(*)
                    FROM items i
                    WHERE (:itemType = '' OR i.type = :itemType)
                      AND (:query = '' OR LOWER(i.title) LIKE LOWER(CONCAT('%', :query, '%')))
                      AND (:genre = '' OR EXISTS (
                          SELECT 1
                          FROM jsonb_array_elements_text(
                              CASE
                                  WHEN jsonb_typeof(i.metadata -> 'genres') = 'array'
                                      THEN i.metadata -> 'genres'
                                  ELSE '[]'::jsonb
                              END
                          ) AS item_genre(value)
                          WHERE LOWER(item_genre.value) = LOWER(:genre)
                      ))
                      AND (:year IS NULL OR COALESCE(i.metadata ->> 'year', i.metadata ->> 'releaseYear') = CAST(:year AS text))
                      AND (:minVote IS NULL OR COALESCE(NULLIF(i.metadata -> 'tmdb' ->> 'voteAverage', '')::double precision, 0) >= :minVote)
                      AND (
                          :ratingStatus = 'all'
                          OR (:ratingStatus = 'rated' AND CAST(:userId AS bigint) IS NOT NULL AND EXISTS (
                              SELECT 1 FROM ratings r WHERE r.item_id = i.id AND r.user_id = CAST(:userId AS bigint)
                          ))
                          OR (:ratingStatus = 'unrated' AND (
                              CAST(:userId AS bigint) IS NULL OR NOT EXISTS (
                                  SELECT 1 FROM ratings r WHERE r.item_id = i.id AND r.user_id = CAST(:userId AS bigint)
                              )
                          ))
                      )
                    """,
            nativeQuery = true
    )
    Page<Item> searchCatalog(
            @Param("itemType") String itemType,
            @Param("query") String query,
            @Param("genre") String genre,
            @Param("year") Integer year,
            @Param("minVote") Double minVote,
            @Param("ratingStatus") String ratingStatus,
            @Param("userId") Long userId,
            Pageable pageable
    );
}
