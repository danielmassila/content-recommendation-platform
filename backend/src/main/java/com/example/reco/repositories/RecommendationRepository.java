package com.example.reco.repositories;

import com.example.reco.model.Recommendation;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.EntityGraph;

public interface RecommendationRepository extends JpaRepository<Recommendation, Long> {

    @Override
    @EntityGraph(attributePaths = {"user", "item"})
    Page<Recommendation> findAll(Pageable pageable);

    @EntityGraph(attributePaths = {"user", "item"})
    Page<Recommendation> findByUserId(Long userId, Pageable pageable);

    @EntityGraph(attributePaths = {"user", "item"})
    Page<Recommendation> findByUserIdAndAlgoVersion(Long userId, String algoVersion, Pageable pageable);
}
