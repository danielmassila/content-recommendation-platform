package com.example.reco.repositories;

import com.example.reco.model.Rating;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface RatingRepository extends JpaRepository<Rating, Long> {
    Page<Rating> findByItemId(Long itemId, Pageable pageable);

    Page<Rating> findByUserId(Long userId, Pageable pageable);

    Optional<Object> findByUserIdAndItemId(Long userId, Long itemId);
}
