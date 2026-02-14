package com.example.reco.repositories;

import com.example.reco.model.Recommendation;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RecommendationRepository extends JpaRepository<Recommendation, Long> {

    Page<Recommendation> findByUserId(Long userId, Pageable pageable);

    Page<Recommendation> findByUserIdAndAlgoVersion(Long userId, String algoVersion, Pageable pageable);
}